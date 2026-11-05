import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]/'skills/orca-team/scripts'
with patch.object(sys, 'path', [str(SCRIPTS)] + sys.path):
    spec = importlib.util.spec_from_file_location('decision', SCRIPTS/'decision.py')
    decision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decision)


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.payload = {'state': {'task': '문서 수정'}, 'questions': {
            'kind': {'type': 'choice', 'instructions': '분류',
                     'criteria': {'simple': '작은 수정', 'build': '기능 구현'}},
            'severity': {'type': 'score', 'instructions': ['심각도'], 'criteria': ['낮음', '높음']},
            'ready': {'type': 'noul', 'instructions': {'question': '완료했는가?'}}}}
        self.response = {'model': 'gpt-6-luna', 'usage': {'input_tokens': 42}, 'answers': [
            {'name': 'ready', 'type': 'predicate', 'probability': 0.7},
            {'name': 'kind', 'type': 'choice', 'choice': 'simple', 'confidence': 0.8,
             'probabilities': [{'value': 'simple', 'probability': 0.8}, {'value': 'build', 'probability': 0.2}]},
            {'name': 'severity', 'type': 'score', 'score': 0.3, 'confidence': 0.7,
             'probabilities': [{'value': 0, 'label': '0', 'probability': 0.7},
                               {'value': 1, 'label': '1', 'probability': 0.3}]}]}

    def test_credential_selection_is_local(self):
        for jev_available, openai_available, expected in [
                (True, True, 'jev'), (True, False, 'jev'),
                (False, True, 'openai'), (False, False, 'none')]:
            with self.subTest(expected=expected), patch.dict(os.environ, {
                    'OPENAI_API_KEY': 'secret-key' if openai_available else ''}), \
                    patch.object(decision.jev, 'credential',
                        side_effect=None if jev_available else decision.jev.JevError('missing_key'),
                        return_value=('secret-key', 'environment')), \
                    patch.object(decision.urllib.request, 'build_opener') as network:
                result = decision.status()
                self.assertEqual(result['selected_provider'], expected)
                self.assertNotIn('secret-key', json.dumps(result))
                self.assertEqual(decision.status('none')['selected_provider'], 'none')
                self.assertEqual(decision.status('openai')['selected_provider'], 'openai')
                network.assert_not_called()

    def test_input_translation_preserves_ids_order_and_payload(self):
        before = copy.deepcopy(self.payload)
        result = decision.openai_request(self.payload)
        self.assertEqual(self.payload, before)
        self.assertEqual(json.loads(result['input']), self.payload['state'])
        self.assertEqual(result['model'], decision.OPENAI_MODEL)
        self.assertEqual([q['name'] for q in result['questions']], ['kind', 'severity', 'ready'])
        self.assertEqual(result['questions'][0]['choices'][0], {'value': 'simple', 'description': '작은 수정'})
        self.assertEqual(result['questions'][1]['levels'],
                         [{'label': '0', 'description': '낮음'}, {'label': '1', 'description': '높음'}])
        self.assertEqual(result['questions'][2]['type'], 'predicate')
        for payload in [dict(self.payload, model='jev-latest'), dict(self.payload, state=float('nan')),
                        dict(self.payload, questions={}), {'state': 'a', 'questions': {'q': None}}]:
            with self.subTest(payload=payload), self.assertRaises(decision.DecisionError):
                decision.openai_request(payload)

    def test_openai_transport_and_raw_result(self):
        stream = io.StringIO(json.dumps(self.response))
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'private-key'}), \
                patch.object(decision.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value = stream
            result = decision.openai_evaluate(self.payload)
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, decision.OPENAI_ENDPOINT)
            self.assertEqual(request.get_header('Authorization'), 'Bearer private-key')
            self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], 30)
            self.assertIsInstance(opener.call_args.args[0], decision.jev.NoRedirect)
            self.assertEqual(json.loads(request.data)['questions'][0]['name'], 'kind')
            self.assertEqual(result['raw'], self.response)
            self.assertEqual(result['answers']['ready']['probability'], 0.7)
            self.assertNotIn('private-key', json.dumps(result))

    def test_invalid_responses_are_not_decisions(self):
        invalid = [None, {}, dict(self.response, answers=[]),
                   dict(self.response, answers=self.response['answers']*2),
                   dict(self.response, usage=None)]
        for field, value in [('name', 'unknown'), ('name', []), ('type', 'refusal'),
                             ('probability', True), ('probability', float('nan')), ('probability', 2)]:
            response = copy.deepcopy(self.response)
            response['answers'][0][field] = value
            invalid.append(response)
        for index, field, value in [(1, 'choice', 'unlisted'), (1, 'probabilities', []),
                                   (2, 'score', -1), (2, 'confidence', float('inf'))]:
            response = copy.deepcopy(self.response)
            response['answers'][index][field] = value
            invalid.append(response)
        request = decision.openai_request(self.payload)
        for response in invalid:
            with self.subTest(response=response), self.assertRaises(decision.DecisionError):
                decision.validate_openai_response(response, request)

    def test_http_errors_timeouts_and_invalid_json(self):
        errors = [(urllib.error.HTTPError(decision.OPENAI_ENDPOINT, code, 'private', {}, None), category)
                  for code, category in [(401, 'authentication_failed'), (403, 'access_denied'),
                                         (429, 'rate_limited'), (302, 'api_error')]]
        errors += [(TimeoutError('private'), 'timeout'), (urllib.error.URLError('private'), 'connection_failed')]
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'private-key'}):
            for error, category in errors:
                with self.subTest(category=category), patch.object(decision.urllib.request, 'build_opener') as opener:
                    opener.return_value.open.side_effect = error
                    with self.assertRaisesRegex(decision.DecisionError, '^' + category) as caught:
                        decision.openai_evaluate(self.payload)
                    self.assertNotIn('private', str(caught.exception))
                    self.assertEqual(opener.return_value.open.call_count, 1)
            with patch.object(decision.urllib.request, 'build_opener') as opener:
                opener.return_value.open.return_value.__enter__.return_value = io.StringIO('not JSON')
                with self.assertRaisesRegex(decision.DecisionError, 'invalid_response'):
                    decision.openai_evaluate(self.payload)

    def test_auto_fallback_once_and_explicit_selection(self):
        raw = {'model': 'jev-latest', 'answers': {'ready': {'value': 0.7}}, 'usage': {}}
        payload = dict(self.payload, model='my-jev-model')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'key'}), \
                patch.object(decision.jev, 'credential', return_value=('key', 'environment')), \
                patch.object(decision.jev, 'evaluate', return_value=raw) as jev_call, \
                patch.object(decision, 'openai_evaluate', return_value={'provider': 'openai'}) as gpt_call:
            result = decision.evaluate(payload)
            self.assertEqual(result['provider'], 'jev')
            self.assertEqual(result['raw'], raw)
            gpt_call.assert_not_called()
            jev_call.side_effect = decision.jev.JevError('authentication_failed: private-key')
            announcements = []
            result = decision.evaluate(payload, announce=lambda *args: announcements.append(args))
            self.assertEqual(result['status'], 'succeeded')
            self.assertEqual(announcements, [('jev', False), ('openai', True)])
            self.assertNotIn('model', gpt_call.call_args.args[0])
            self.assertEqual(payload['model'], 'my-jev-model')
            gpt_call.reset_mock()
            self.assertEqual(decision.evaluate(payload, 'jev')['status'], 'coordinator_required')
            gpt_call.assert_not_called()
            gpt_call.side_effect = decision.DecisionError('timeout: private-key')
            result = decision.evaluate(payload)
            self.assertEqual(result['status'], 'coordinator_required')
            self.assertEqual(len(result['attempts']), 2)
            self.assertEqual(gpt_call.call_count, 1)
            self.assertNotIn('private-key', json.dumps(result))
            jev_call.reset_mock()
            result = decision.evaluate(self.payload, 'openai')
            self.assertEqual(result['status'], 'coordinator_required')
            jev_call.assert_not_called()

    def test_no_provider_or_disabled_makes_no_request(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), \
                patch.object(decision.jev, 'credential', side_effect=decision.jev.JevError('missing_key')), \
                patch.object(decision.jev, 'evaluate') as jev_call, \
                patch.object(decision, 'openai_evaluate') as gpt_call:
            for provider in ('auto', 'none'):
                result = decision.evaluate(self.payload, provider)
                self.assertEqual(result['status'], 'coordinator_required')
                self.assertEqual(result['attempts'], [])
            jev_call.assert_not_called()
            gpt_call.assert_not_called()

    def test_only_openai_and_missing_explicit_credentials(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'key'}), \
                patch.object(decision.jev, 'credential', side_effect=decision.jev.JevError('missing_key')), \
                patch.object(decision.jev, 'evaluate') as jev_call, \
                patch.object(decision, 'openai_evaluate', return_value={'provider': 'openai'}) as gpt_call:
            self.assertEqual(decision.evaluate(self.payload)['provider'], 'openai')
            self.assertEqual(gpt_call.call_count, 1)
            jev_call.assert_not_called()
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), \
                patch.object(decision.urllib.request, 'build_opener') as network:
            result = decision.evaluate(self.payload, 'openai')
            self.assertEqual(result['attempts'][0]['reason'], 'missing_key')
            network.assert_not_called()

    def test_kit_accepts_and_rejects_decision_config(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)/'.config/orca-orchestration-kit'
            state.mkdir(parents=True)
            root = SCRIPTS.parents[2]
            command = [sys.executable, str(root/'kit.py'), 'route', '--home', directory,
                       '--task-type', 'implementation', '--candidates']
            for section, valid in [({}, True)] + [({'provider': p}, True) for p in decision.PROVIDERS] + [
                    (None, False), ([], False), ({'provider': 'bad'}, False),
                    ({'provider': True}, False), ({'extra': 'bad'}, False)]:
                with self.subTest(section=section):
                    (state/'config.json').write_text(json.dumps({'decision': section}), encoding='utf-8')
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0 if valid else 1, result.stderr)
                    if valid:
                        self.assertIn('candidates', json.loads(result.stdout))
                    else:
                        self.assertIn('decision.provider', result.stderr)

    def test_cli_config_and_override(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home/'.config/orca-orchestration-kit/config.json'
            path.parent.mkdir(parents=True)
            cmd = [sys.executable, str(SCRIPTS/'decision.py')]
            for provider in decision.PROVIDERS:
                path.write_text(json.dumps({'decision': {'provider': provider}}), encoding='utf-8')
                result = subprocess.run(cmd+['status', '--home', directory], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['requested_provider'], provider)
            result = subprocess.run(cmd+['status', '--home', directory, '--provider', 'openai'],
                                    capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)['selected_provider'], 'openai')
            result = subprocess.run(cmd+['evaluate', '--home', directory, '--provider', 'none'],
                                    input=json.dumps(self.payload), capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['reason'], 'disabled')
            for section in [None, 'jev', {'provider': 'invalid'}, {'provider': []}, {'extra': True}]:
                path.write_text(json.dumps({'decision': section}), encoding='utf-8')
                result = subprocess.run(cmd+['status', '--home', directory], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('invalid_config', result.stderr)

    def test_installed_client_includes_jev_and_config(self):
        from test_kit import kit
        with tempfile.TemporaryDirectory() as directory:
            # macOS /var is a symlink; install intentionally rejects symlink ancestors.
            root = Path(directory).resolve()
            home = root/'home'
            state = home/'.config/orca-orchestration-kit'
            state.mkdir(parents=True)
            (state/'config.json').write_text('{"decision":{"provider":"none"}}', encoding='utf-8')
            destination = root/'skills'
            kit.install(SCRIPTS.parent, {'test': destination}, state)
            client = destination/'orca-team/scripts/decision.py'
            self.assertEqual(client.read_bytes(), (SCRIPTS/'decision.py').read_bytes())
            result = subprocess.run([sys.executable, str(client), 'status', '--home', str(home)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['selected_provider'], 'none')


if __name__ == '__main__':
    unittest.main()
