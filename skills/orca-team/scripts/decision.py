#!/usr/bin/env python3
"""Optional Jev/OpenAI decision support; never logs credentials or request bodies."""

import argparse
import copy
import json
import math
import os
from pathlib import Path
import socket
import sys
import urllib.error
import urllib.request

import jev

PROVIDERS = ('auto', 'jev', 'openai', 'none')
OPENAI_ENDPOINT = 'https://api.openai.com/v1/decisions'
OPENAI_MODEL = 'gpt-6-luna'


class DecisionError(Exception):
    pass


def configured_provider(config):
    section = config.get('decision', {})
    if (not isinstance(section, dict) or set(section) - {'provider'}
            or section.get('provider', 'auto') not in PROVIDERS):
        raise DecisionError('invalid_config: decision.provider must be auto, jev, openai, or none')
    return section.get('provider', 'auto')


def status(provider='auto'):
    if provider not in PROVIDERS:
        raise DecisionError('invalid_provider')
    try:
        _, source = jev.credential()
        jev_status = {'configured': True, 'source': source}
    except jev.JevError:
        jev_status = {'configured': False}
    available = {'jev': jev_status,
                 'openai': {'configured': bool(os.environ.get('OPENAI_API_KEY', '').strip())}}
    selected = provider
    if selected == 'auto':
        selected = next((p for p in ('jev', 'openai') if available[p]['configured']), 'none')
    return {'requested_provider': provider, 'selected_provider': selected,
            'configured': selected != 'none' and available[selected]['configured'],
            'availability': 'credential presence only; API access unverified',
            'providers': available}


def validate_input(payload):
    try:
        result = jev.validate_request(copy.deepcopy(payload))
        # Validate finite JSON even when no provider is configured.
        json.dumps(result, ensure_ascii=False, allow_nan=False)
    except (jev.JevError, ValueError, TypeError, UnicodeError):
        raise DecisionError('invalid_input: expected finite JSON with state and valid questions') from None
    if any(not isinstance(name, str) or not name.strip() for name in result['questions']):
        raise DecisionError('invalid_input: question names must be nonempty strings')
    return result


def as_text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, allow_nan=False)


def openai_request(payload):
    checked = validate_input(payload)
    model = payload.get('model', OPENAI_MODEL)
    if model != OPENAI_MODEL:
        raise DecisionError('invalid_model: Decisions currently supports gpt-6-luna only')
    if len(checked['questions']) > 400:
        raise DecisionError('invalid_input: OpenAI supports at most 400 questions')
    questions = []
    for name, question in checked['questions'].items():
        kind = question['type']
        item = {'name': name, 'type': 'predicate' if kind == 'noul' else kind,
                'instructions': as_text(question['instructions'])}
        if kind == 'choice':
            criteria = question['criteria']
            if any(not isinstance(k, str) or not k for k in criteria):
                raise DecisionError('invalid_input: choice keys must be nonempty strings')
            item['choices'] = [{'value': k, 'description': as_text(v)} for k, v in criteria.items()]
        elif kind == 'score':
            item['levels'] = []
            for index, criterion in enumerate(question['criteria']):
                # Preserve ordered criteria as descriptions; labels identify their original indices.
                item['levels'].append({'label': str(index), 'description': as_text(criterion)})
        questions.append(item)
    return {'model': model, 'input': as_text(checked['state']), 'questions': questions}


def number(value, maximum=1):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum


def validate_openai_response(result, request):
    if (not isinstance(result, dict) or not isinstance(result.get('answers'), list)
            or not isinstance(result.get('model'), str) or not result['model'].strip()
            or not isinstance(result.get('usage'), dict)):
        raise DecisionError('invalid_response: expected answers, model, and usage')
    expected = {q['name']: q for q in request['questions']}
    answers = {}
    for answer in result['answers']:
        if not isinstance(answer, dict):
            raise DecisionError('invalid_response: expected named answers')
        name = answer.get('name')
        if not isinstance(name, str) or name not in expected or name in answers:
            raise DecisionError('invalid_response: unknown or duplicate question name')
        if answer.get('type') == 'refusal':
            raise DecisionError('refused: provider declined a question; coordinator judgement required')
        question = expected[name]
        kind = question['type']
        valid = answer.get('type') == kind
        if kind == 'predicate':
            valid = valid and number(answer.get('probability'))
        else:
            valid = valid and number(answer.get('confidence'))
            probabilities = answer.get('probabilities')
            options = ([c['value'] for c in question['choices']] if kind == 'choice'
                       else list(range(len(question['levels']))))
            if not isinstance(probabilities, list) or len(probabilities) != len(options):
                valid = False
            else:
                values = []
                for entry in probabilities:
                    if not isinstance(entry, dict) or not number(entry.get('probability')):
                        valid = False
                        break
                    value = entry.get('value')
                    if (type(value) is not (str if kind == 'choice' else int)
                            or value not in options or value in values):
                        valid = False
                    values.append(value)
                if valid and not math.isclose(sum(p['probability'] for p in probabilities), 1, abs_tol=1e-5):
                    valid = False
            if kind == 'choice':
                valid = valid and type(answer.get('choice')) is str and answer['choice'] in options
            else:
                valid = valid and number(answer.get('score'), len(options) - 1)
        if not valid:
            raise DecisionError('invalid_response: answer type, value, or probabilities are invalid')
        answers[name] = answer
    if set(answers) != set(expected):
        raise DecisionError('invalid_response: answer IDs differ from requested questions')
    return answers


def openai_evaluate(payload):
    request_body = openai_request(payload)
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise DecisionError('missing_key: set OPENAI_API_KEY in your environment')
    try:
        request = urllib.request.Request(OPENAI_ENDPOINT,
            data=json.dumps(request_body, ensure_ascii=False, allow_nan=False).encode('utf-8'),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.build_opener(jev.NoRedirect()).open(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        category = {401: 'authentication_failed', 403: 'access_denied', 429: 'rate_limited'}.get(error.code, 'api_error')
        raise DecisionError(category + ': HTTP ' + str(error.code)) from None
    except (socket.timeout, TimeoutError):
        raise DecisionError('timeout: 30-second limit') from None
    except (urllib.error.URLError, OSError):
        raise DecisionError('connection_failed') from None
    except (ValueError, UnicodeError):
        raise DecisionError('invalid_response: invalid JSON') from None
    answers = validate_openai_response(result, request_body)
    return {'provider': 'openai', 'model': result['model'], 'answers': answers,
            'usage': result['usage'], 'raw': result}


def evaluate(payload, provider='auto', announce=None):
    validate_input(payload)
    info = status(provider)
    selected = info['selected_provider']
    if selected == 'none':
        return {'status': 'coordinator_required', 'provider': 'none',
                'reason': 'disabled' if provider == 'none' else 'no configured decision provider',
                'attempts': []}
    candidates = [selected]
    if provider == 'auto' and selected == 'jev' and info['providers']['openai']['configured']:
        candidates.append('openai')
    attempts = []
    for index, candidate in enumerate(candidates):
        if announce:
            announce(candidate, index > 0)
        request = copy.deepcopy(payload)
        if index > 0:
            request.pop('model', None)
        try:
            if candidate == 'openai':
                result = openai_evaluate(request)
            else:
                raw = jev.evaluate(request)
                result = {'provider': 'jev', 'model': raw.get('model'), 'answers': raw['answers'],
                          'usage': raw.get('usage'), 'raw': raw}
            attempts.append({'provider': candidate, 'status': 'succeeded'})
            return dict(result, status='succeeded', attempts=attempts)
        except (jev.JevError, DecisionError) as error:
            # Only the category is retained; provider errors and response bodies can contain secrets.
            attempts.append({'provider': candidate, 'status': 'failed',
                             'reason': str(error).split(':', 1)[0]})
    return {'status': 'coordinator_required', 'provider': 'none',
            'reason': 'decision providers failed; no automatic retry', 'attempts': attempts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['status', 'evaluate'])
    parser.add_argument('--provider', choices=PROVIDERS)
    parser.add_argument('--input', default='-')
    parser.add_argument('--home', type=Path, default=Path.home())
    args = parser.parse_args()
    try:
        path = args.home / '.config/orca-orchestration-kit/config.json'
        config = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if not isinstance(config, dict):
            raise DecisionError('invalid_config: expected an object')
        configured = configured_provider(config)
        provider = args.provider if args.provider is not None else configured
        if args.command == 'status':
            result = status(provider)
        else:
            if args.input == '-':
                payload = json.load(sys.stdin)
            else:
                payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
            def announce(candidate, fallback):
                prefix = 'Jev 판단 실패: 같은 발췌로 대체 호출' if fallback else '보조 판단 호출'
                print(prefix + ' → ' + candidate, file=sys.stderr)
            result = evaluate(payload, provider, announce)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0 if result.get('status') != 'coordinator_required' else 1
    except DecisionError as error:
        print(str(error), file=sys.stderr)
    except (ValueError, OSError, UnicodeError, TypeError):
        print('local_error: check configuration and input JSON; no request retry', file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print('cancelled: no request retry', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
