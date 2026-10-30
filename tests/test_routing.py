import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_kit import kit

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.state=Path(self.tmp.name)
        self.identity={'path':'test','mtime_ns':1,'size':1}
        self.mock=patch.object(kit,'tool_identity',return_value=self.identity);self.mock.start();self.addCleanup(self.mock.stop)
        self.profiles,_=kit.routing_config({})
        self.evidence={kit.profile_key(p):{'identity':self.identity,'verified_at':kit.datetime.now(kit.timezone.utc).isoformat(),'dispatch_id':'test'} for p in self.profiles.values()}
        self.save()
    def save(self):kit.write_json(self.state/'model-evidence.json',self.evidence)
    def route(self,t='implementation',**kw):return kit.route({},self.state,t,**kw)
    def test_types_and_encoding(self):
        for t,p,e in [('simple','light','low'),('implementation','standard','medium'),('design','deep','high'),('review','review','high')]:
            result=self.route(t);self.assertEqual(result['profile'],p);self.assertEqual(result['effort'],e)
        self.assertNotIn('--effort',self.route('simple')['launch_args'])
        self.assertIn('--effort',self.route()['launch_args'])
        self.assertEqual(self.route(complexity='complex')['profile'],'deep')
    def test_stale_and_explicit_no_fallback(self):
        self.evidence.pop(kit.profile_key(self.profiles['light']));self.save()
        self.assertEqual(self.route('simple')['profile'],'standard')
        self.assertEqual(self.route('simple',profile='light')['status'],'blocked')
        self.evidence[kit.profile_key(self.profiles['standard'])]['verified_at']='2000-01-01T00:00:00+00:00';self.save()
        self.assertEqual(self.route()['status'],'blocked')
    def test_upgrade_once_and_quality_only(self):
        prior=self.route()
        for failure in ['auth','network','installation']:
            self.assertEqual(self.route(prior=prior,failure=failure,settled=True)['status'],'blocked')
        self.assertEqual(self.route(prior=prior,failure='quality')['status'],'blocked')
        upgrade=self.route(prior=prior,failure='quality',settled=True)
        self.assertEqual(upgrade['profile'],'deep');self.assertEqual(upgrade['upgrades'],1)
        self.assertEqual(self.route(prior=upgrade,failure='quality',settled=True)['status'],'blocked')
    def test_config_and_explicit_precedence(self):
        config={'routes':{'implementation':'deep'}}
        self.assertEqual(kit.route(config,self.state,'implementation')['profile'],'deep')
        self.assertEqual(kit.route(config,self.state,'implementation',profile='standard')['profile'],'standard')
        self.assertEqual(self.route(model='missing')['status'],'blocked')
        with self.assertRaises(ValueError):self.route('simple',effort='high')
        with self.assertRaises(ValueError):kit.routing_config({'profiles':[]})
        p=dict(self.profiles['light'],fallback='light')
        with self.assertRaises(ValueError):kit.routing_config({'profiles':{'light':p}})
    def test_changed_or_missing_tool_and_review(self):
        with patch.object(kit,'tool_identity',return_value=None):self.assertEqual(self.route()['status'],'blocked')
        with patch.object(kit,'tool_identity',return_value={'path':'new'}):self.assertEqual(self.route()['status'],'blocked')
        self.assertTrue(self.route('review',implementation_agent='codex')['review_independence'])
        self.assertFalse(self.route('review',implementation_agent='agy')['review_independence'])
