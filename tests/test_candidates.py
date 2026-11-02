import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import test_routing


class CandidateTests(unittest.TestCase):
    setUp=test_routing.RoutingTests.setUp
    save=test_routing.RoutingTests.save
    def select(self, name='claude-opus', task='design', config=None, **kw):
        return self.kit_select(config or {}, task, name, **kw)

    def kit_select(self, config, task, name, **kw):
        from test_kit import kit
        return kit.select_candidate(config,self.state,task,name,'task-specific rationale',**kw)

    def quota(self, agent, remaining):
        from test_kit import kit
        kit.usage.observe(self.state,agent,agent,agent,remaining,300,time.time()+1000)

    def test_listing_read_only_and_claude(self):
        from test_kit import kit
        before={p.name:p.read_bytes() for p in self.state.iterdir()}
        result=kit.route_candidates({},self.state,'design')
        self.assertEqual(result['baseline_profile'],'deep')
        self.assertTrue({'claude-sonnet','claude-opus','claude-fable'}<={p['profile'] for p in result['candidates']})
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.state.iterdir()})
        self.assertEqual(self.select()['profile'],'claude-opus')
        self.assertFalse(self.select()['explicit'])
        self.assertEqual(self.select()['selection_reason'],'task-specific rationale')

    def test_validation_and_custom_baseline(self):
        from test_kit import kit
        for config in [{'candidates':[]},{'candidates':{'design':[]}},{'candidates':{'design':['missing']}},{'candidates':{'unknown':['deep']}}]:
            with self.assertRaises(ValueError):kit.routing_config(config)
        config={'routes':{'implementation':'claude-sonnet'},'candidates':{'implementation':['standard']}}
        self.assertEqual(kit.candidate_names(config,'implementation'),['claude-sonnet','standard'])
        self.assertEqual(kit.candidate_names({},'implementation','complex')[0],'deep')
        with self.assertRaises(ValueError):kit.select_candidate({},self.state,'simple','claude-opus','reason')
        with self.assertRaises(ValueError):kit.select_candidate({},self.state,'design','claude-opus',' ')

    def test_missing_stale_and_changed_claude(self):
        from test_kit import kit
        key=kit.profile_key(self.profiles['claude-opus'])
        self.evidence[key]['verified_at']='2000-01-01T00:00:00+00:00';self.save()
        self.assertEqual(self.select()['status'],'blocked')
        self.evidence.pop(key);self.save()
        row=next(p for p in kit.route_candidates({},self.state,'design')['candidates'] if p['profile']=='claude-opus')
        self.assertEqual(row['verification_status'],'blocked');self.assertTrue(row['excluded_reasons'])
        self.assertEqual(self.select('deep')['status'],'ready')
        with patch.object(kit,'tool_identity',return_value={'path':'changed'}):
            self.assertEqual(self.select('deep')['status'],'blocked')

    def test_quota_selection_and_explicit_preservation(self):
        from test_kit import kit
        self.quota('claude',80)
        self.assertEqual(self.select()['profile'],'claude-opus')
        self.quota('claude',20)
        # Unknown quota is not spare capacity.
        self.assertEqual(self.select()['profile'],'claude-opus')
        self.quota('codex',80)
        self.assertEqual(self.select()['profile'],'deep')
        self.quota('claude',5)
        selected=self.select()
        self.assertEqual(selected['profile'],'deep');self.assertEqual(selected['selected_profile'],'claude-opus')
        self.assertIn('usage_reason',selected)
        self.assertEqual(kit.route({},self.state,'design',profile='claude-opus')['status'],'blocked')
        self.quota('codex',5)
        self.assertEqual(self.select()['status'],'blocked')
        self.assertEqual(self.select()['launch_args'],[])

    def test_task_approval_not_effort_ranking_and_independence(self):
        from test_kit import kit
        self.quota('claude',10);self.quota('codex',80)
        config={'candidates':{'review':['claude-sonnet','standard']}}
        result=self.select('claude-sonnet',task='review',config=config,implementation_agent='agy')
        self.assertEqual(result['profile'],'standard')
        self.assertTrue(result['review_independence'])
        self.assertIsNone(kit.route_candidates({},self.state,'review')['candidates'][0]['review_independence'])
        self.quota('claude',80)
        self.assertFalse(self.select(task='review',implementation_agent='claude')['review_independence'])

    def test_cli_modes_and_installed_script_parity(self):
        from test_kit import kit
        root=Path(kit.__file__).parent
        for name in ['kit.py','usage.py']:
            self.assertEqual((root/name).read_bytes(),(root/'skills/orca-team/scripts'/name).read_bytes())
        home=self.state/'home'
        cmd=[sys.executable,str(root/'kit.py'),'route','--home',str(home),'--task-type','design']
        before=list(self.state.rglob('*'))
        result=subprocess.run(cmd+['--candidates'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(json.loads(result.stdout)['candidates']),10)
        self.assertEqual(before,list(self.state.rglob('*')))
        for flags in [['--candidates','--profile','deep'],['--select-profile','claude-opus'],['--selection-reason','alone']]:
            self.assertNotEqual(subprocess.run(cmd+flags,capture_output=True).returncode,0)

    def test_claude_models_are_separate_candidates(self):
        from test_kit import kit
        for task in ['implementation','test','design','debug','review']:
            names=kit.candidate_names({},task)
            self.assertTrue({'claude-sonnet','claude-opus','claude-fable'}<=set(names),task)
        self.assertFalse(any(n.startswith('claude') for n in kit.candidate_names({},'simple')))
        models={n:self.profiles[n]['model'] for n in ['claude-sonnet','claude-opus','claude-fable']}
        self.assertEqual(models,{'claude-sonnet':'sonnet','claude-opus':'opus','claude-fable':'fable'})
        kit.usage.observe(self.state,'claude','claude','claude',80,300,time.time()+1000)
        kit.usage.observe(self.state,'claude','claude','claude-fable',80,10080,time.time()+1000)
        for name in models:
            result=self.select(name)
            self.assertEqual(result['profile'],name)
            self.assertEqual(result['launch_args'][result['launch_args'].index('--model')+1],models[name])
        # Fable has its own weekly window; a low Fable window must not be hidden by the shared one.
        kit.usage.observe(self.state,'claude','claude','claude',80,300,time.time()+1000)
        kit.usage.observe(self.state,'claude','claude','claude-fable',4,10080,time.time()+1000)
        self.assertEqual(kit.usage.status(self.state,self.profiles['claude-fable'],{})['state'],'protected')
        self.assertEqual(kit.usage.status(self.state,self.profiles['claude-opus'],{})['state'],'normal')

    def test_fable_requires_reported_quota_for_automatic_choice(self):
        from test_kit import kit
        # Accounts without a Fable allowance report no fableWeekly window.
        kit.usage.observe(self.state,'claude','claude','claude',80,300,time.time()+1000)
        row=next(r for r in kit.route_candidates({},self.state,'design')['candidates'] if r['profile']=='claude-fable')
        self.assertEqual(row['status'],'blocked')
        self.assertTrue(any('claude-fable' in r for r in row['excluded_reasons']))
        self.assertEqual(self.select('claude-fable')['status'],'blocked')
        self.assertEqual(self.select('claude-opus')['status'],'ready')
        # The user's explicit choice is not hidden by the automatic gate.
        self.assertEqual(kit.route({},self.state,'design',profile='claude-fable')['status'],'ready')
        kit.usage.observe(self.state,'claude','claude','claude-fable',70,10080,time.time()+1000)
        self.assertEqual(self.select('claude-fable')['status'],'ready')
        with self.assertRaises(ValueError):kit.routing_config({'profiles':{'x':{'agent':'claude','model':'fable','effort':'high','effort_mode':'flag','require_quota':True}}})

    def test_coordinator_effort_needs_verified_combination(self):
        from test_kit import kit
        self.assertEqual(self.select('claude-sonnet',effort='medium')['status'],'blocked')
        row=next(r for r in kit.route_candidates({},self.state,'implementation')['candidates'] if r['profile']=='claude-sonnet')
        self.assertEqual(row['verified_efforts'],['high'])
        self.evidence[kit.profile_key({**self.profiles['claude-sonnet'],'effort':'medium'})]=dict(self.evidence[kit.profile_key(self.profiles['claude-sonnet'])]);self.save()
        result=self.select('claude-sonnet',effort='medium')
        self.assertEqual(result['status'],'ready');self.assertEqual(result['selected_effort'],'medium')
        self.assertEqual(result['launch_args'][-2:],['--effort','medium'])
        for bad in [('claude-sonnet','max'),('review','medium')]:
            with self.assertRaises(ValueError):self.select(bad[0],task='review',effort=bad[1])

    def test_review_quota_fallback_prefers_independent_tool(self):
        self.quota('claude',5);self.quota('agy',80);self.quota('codex',80)
        from test_kit import kit
        # Model-specific AGY windows must be known before it counts as spare.
        for group in ['Gemini Models','Gemini 4 Argon']:
            kit.usage.observe(self.state,'agy','agy',group,80,300,time.time()+1000)
        selected=self.select(task='review',implementation_agent='agy')
        self.assertEqual(selected['profile'],'deep')
        self.assertTrue(selected['review_independence'])

    def test_agy_multimodel_candidates(self):
        from test_kit import kit
        agy_profiles = ['gemini-flash','gemini-argon','agy-claude-sonnet','agy-claude-opus','agy-gpt-oss']
        for name in agy_profiles:
            self.assertIn(name, self.profiles)
            self.assertEqual(self.profiles[name]['agent'], 'agy')
            self.assertEqual(self.profiles[name]['effort_mode'], 'flag')

        # simple task includes light and gemini-flash, but not heavy models
        simple_candidates = kit.candidate_names({}, 'simple')
        self.assertIn('gemini-flash', simple_candidates)
        self.assertNotIn('gemini-argon', simple_candidates)
        self.assertNotIn('agy-claude-sonnet', simple_candidates)

        # implementation includes gemini-flash, gemini-argon, agy-claude-sonnet, agy-gpt-oss
        impl_candidates = kit.candidate_names({}, 'implementation')
        self.assertTrue({'gemini-flash','gemini-argon','agy-claude-sonnet','agy-gpt-oss'} <= set(impl_candidates))

        # design includes gemini-argon, agy-claude-opus, agy-claude-sonnet
        design_candidates = kit.candidate_names({}, 'design')
        self.assertTrue({'gemini-argon','agy-claude-opus','agy-claude-sonnet'} <= set(design_candidates))

        # Launch args use agent 'antigravity' and flag effort
        for group in ['Gemini Models','Gemini 4 Argon','Claude and GPT models']:
            kit.usage.observe(self.state, 'agy', 'agy', group, 80, 300, time.time()+1000)
        res = self.select('gemini-flash', task='implementation')
        self.assertEqual(res['launch_args'], ['--agent','antigravity','--model','gemini-3.8-flash','--effort','medium'])

        res_claude = self.select('agy-claude-sonnet', task='implementation')
        self.assertEqual(res_claude['launch_args'], ['--agent','antigravity','--model','claude-sonnet-5-5','--effort','high'])

    def test_agy_coordinator_effort_selection(self):
        from test_kit import kit
        for group in ['Gemini Models','Gemini 4 Argon','Claude and GPT models']:
            kit.usage.observe(self.state, 'agy', 'agy', group, 80, 300, time.time()+1000)

        # Before low effort is verified for gemini-flash, selecting low is blocked
        self.assertEqual(self.select('gemini-flash', task='implementation', effort='low')['status'], 'blocked')

        # Verify low effort
        self.evidence[kit.profile_key({**self.profiles['gemini-flash'], 'effort': 'low'})] = dict(self.evidence[kit.profile_key(self.profiles['gemini-flash'])])
        self.save()

        res = self.select('gemini-flash', task='implementation', effort='low')
        self.assertEqual(res['status'], 'ready')
        self.assertEqual(res['launch_args'][-2:], ['--effort', 'low'])

    def test_agy_quota_isolation_across_groups(self):
        from test_kit import kit
        # Observe normal Gemini Models and Claude and GPT models, but protected Argon
        kit.usage.observe(self.state, 'agy', 'agy', 'Gemini Models', 80, 300, time.time()+1000)
        kit.usage.observe(self.state, 'agy', 'agy', 'Claude and GPT models', 80, 300, time.time()+1000)
        kit.usage.observe(self.state, 'agy', 'agy', 'Gemini 4 Argon', 4, 10080, time.time()+1000)

        # Argon is blocked due to protected quota, but gemini-flash and agy-claude-sonnet are normal
        self.assertEqual(kit.usage.status(self.state, self.profiles['gemini-argon'], {})['state'], 'protected')
        self.assertEqual(kit.usage.status(self.state, self.profiles['gemini-flash'], {})['state'], 'normal')
        self.assertEqual(kit.usage.status(self.state, self.profiles['agy-claude-sonnet'], {})['state'], 'normal')

        # When Claude and GPT models is protected, agy-claude and agy-gpt are protected, but gemini-flash is unaffected
        kit.usage.observe(self.state, 'agy', 'agy', 'Claude and GPT models', 3, 300, time.time()+1000)
        self.assertEqual(kit.usage.status(self.state, self.profiles['agy-claude-sonnet'], {})['state'], 'protected')
        self.assertEqual(kit.usage.status(self.state, self.profiles['agy-gpt-oss'], {})['state'], 'protected')
        self.assertEqual(kit.usage.status(self.state, self.profiles['gemini-flash'], {})['state'], 'normal')

    def test_grok_candidates_and_launch(self):
        from test_kit import kit
        for name, model in [('grok-4.5','grok-4.5'),('grok-4.6','grok-4.6'),('grok-4.7','grok-4.7')]:
            self.assertEqual(self.profiles[name]['agent'], 'grok')
            self.assertEqual(self.profiles[name]['model'], model)
            self.assertEqual(self.profiles[name]['effort'], 'high')
            self.assertEqual(self.profiles[name]['quota_groups'], ['grok'])
        simple = kit.candidate_names({}, 'simple')
        self.assertIn('grok-4.5', simple)
        self.assertNotIn('grok-4.6', simple)
        self.assertNotIn('grok-4.7', simple)
        design = set(kit.candidate_names({}, 'design'))
        self.assertTrue({'grok-4.6','grok-4.7'} <= design)
        self.assertNotIn('grok-4.5', design)
        self.assertEqual(kit.route_candidates({}, self.state, 'design')['baseline_profile'], 'deep')
        kit.usage.observe(self.state, 'grok', 'grok', 'grok', 80, 10080, time.time()+1000)
        res = self.select('grok-4.7', task='design')
        self.assertEqual(res['launch_args'], ['--agent','grok','--model','grok-4.7','--effort','high'])
        self.assertFalse(self.select('grok-4.7', task='review', implementation_agent='grok')['review_independence'])
        with self.assertRaises(ValueError):
            self.select('grok-4.7', task='design', effort='xhigh')
