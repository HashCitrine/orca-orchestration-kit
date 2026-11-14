import unittest
from pathlib import Path
from unittest.mock import patch
import test_routing


class ExtendedAgentTests(unittest.TestCase):
    setUp = test_routing.RoutingTests.setUp
    save = test_routing.RoutingTests.save

    def config(self):
        return {
            'profiles': {
                'opencode-default': {
                    'agent': 'opencode',
                    'model': 'openai/gpt-5.4',
                    'effort': 'default',
                    'effort_mode': 'none',
                },
                'pi-high': {
                    'agent': 'pi',
                    'model': 'openai/gpt-5.4',
                    'effort': 'high',
                    'effort_mode': 'flag',
                },
                'omp-high': {
                    'agent': 'omp',
                    'model': 'openai/gpt-5.4',
                    'effort': 'high',
                    'effort_mode': 'flag',
                },
            },
            'candidates': {'implementation': ['opencode-default', 'pi-high', 'omp-high']},
        }

    def add_evidence(self, config):
        from test_kit import kit
        profiles, _ = kit.routing_config(config)
        for name in ('opencode-default', 'pi-high', 'omp-high'):
            record = {
                'identity': self.identity,
                'verified_at': kit.datetime.now(kit.timezone.utc).isoformat(),
                'dispatch_id': 'test',
            }
            self.evidence[kit.profile_key(profiles[name])] = record
            if name in ('pi-high', 'omp-high'):
                self.evidence[kit.profile_key({**profiles[name], 'effort': 'medium'})] = record
        self.save()

    def test_skill_roots(self):
        from test_kit import kit
        root = Path(self.tmp.name)
        with patch.dict(kit.os.environ, {}, clear=True):
            roots = kit.roots(root, {})
        self.assertEqual(roots['opencode'], root/'.config/opencode/skills')
        self.assertEqual(roots['pi'], root/'.pi/agent/skills')
        self.assertEqual(roots['omp'], root/'.agents/skills')
        with patch.dict(kit.os.environ, {'XDG_CONFIG_HOME': str(root/'xdg'),
                                         'PI_CODING_AGENT_DIR': str(root/'pi-home')}, clear=True):
            roots = kit.roots(root, {})
        self.assertEqual(roots['opencode'], root/'xdg/opencode/skills')
        self.assertEqual(roots['pi'], root/'pi-home/skills')
        self.assertEqual(roots['omp'], root/'.agents/skills')

    def test_launch_and_candidates(self):
        from test_kit import kit
        config = self.config()
        self.add_evidence(config)
        opencode = kit.route(config, self.state, 'implementation', profile='opencode-default')
        self.assertEqual(opencode['status'], 'ready')
        self.assertEqual(opencode['launch_args'],
                         ['--agent', 'opencode', '--model', 'openai/gpt-5.4'])
        pi = kit.route(config, self.state, 'implementation', profile='pi-high')
        self.assertEqual(pi['status'], 'ready')
        self.assertEqual(pi['launch_args'],
                         ['--agent', 'pi', '--model', 'openai/gpt-5.4', '--effort', 'high'])
        omp = kit.route(config, self.state, 'implementation', profile='omp-high')
        self.assertEqual(omp['status'], 'ready')
        self.assertEqual(omp['launch_args'],
                         ['--agent', 'omp', '--model', 'openai/gpt-5.4', '--effort', 'high'])
        rows = {row['profile']: row for row in
                kit.route_candidates(config, self.state, 'implementation')['candidates']}
        self.assertEqual(rows['opencode-default']['verified_efforts'], ['default'])
        self.assertEqual(rows['pi-high']['verified_efforts'], ['medium', 'high'])
        self.assertEqual(rows['omp-high']['verified_efforts'], ['medium', 'high'])
        self.assertEqual(kit.select_candidate(config, self.state, 'implementation',
                                              'opencode-default', 'reason')['status'], 'ready')
        override = kit.route(config, self.state, 'implementation', agent='opencode', model='openai/gpt-5.4')
        self.assertEqual(override['status'], 'ready')
        self.assertEqual(override['launch_args'], ['--agent', 'opencode', '--model', 'openai/gpt-5.4'])
        self.assertEqual(kit.route(config, self.state, 'implementation', agent='opencode',
                                   model='openai/gpt-5.4', effort='high')['status'], 'blocked')
        pi_override = kit.route(config, self.state, 'implementation', agent='pi', model='openai/gpt-5.4')
        self.assertEqual(pi_override['status'], 'ready')
        self.assertEqual(pi_override['launch_args'], ['--agent', 'pi', '--model', 'openai/gpt-5.4', '--effort', 'medium'])
        omp_override = kit.route(config, self.state, 'implementation', agent='omp', model='openai/gpt-5.4')
        self.assertEqual(omp_override['status'], 'ready')
        self.assertEqual(omp_override['launch_args'], ['--agent', 'omp', '--model', 'openai/gpt-5.4', '--effort', 'medium'])
        omp_embedded = kit.route(config, self.state, 'review', agent='omp', model='openai/gpt-5.4')
        self.assertEqual(omp_embedded['status'], 'ready')
        self.assertEqual(omp_embedded['effort_mode'], 'flag')
        self.assertEqual(omp_embedded['launch_args'], ['--agent', 'omp', '--model', 'openai/gpt-5.4', '--effort', 'high'])

    def test_invalid_effort_modes(self):
        from test_kit import kit
        profiles = [
            {'agent': 'opencode', 'model': 'm', 'effort': 'high', 'effort_mode': 'flag'},
            {'agent': 'opencode', 'model': 'm', 'effort': 'high', 'effort_mode': 'none'},
            {'agent': 'pi', 'model': 'm', 'effort': 'default', 'effort_mode': 'none'},
            {'agent': 'pi', 'model': 'm', 'effort': 'high', 'effort_mode': 'embedded'},
            {'agent': 'omp', 'model': 'm-high', 'effort': 'high', 'effort_mode': 'embedded'},
            {'agent': 'codex', 'model': 'm', 'effort': 'default', 'effort_mode': 'none'},
        ]
        for profile in profiles:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                kit.routing_config({'profiles': {'x': profile}})


if __name__ == '__main__':
    unittest.main()
