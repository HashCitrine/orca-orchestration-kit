import copy
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from test_kit import kit

class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.state=self.root/'state'
        now=datetime.now(timezone.utc)
        self.identity={'path':'test','mtime_ns':int((now-timedelta(hours=1)).timestamp()*1e9),'size':42}
        kit.write_json(self.state/'setup-observation.json',{'observed_at':(now-timedelta(minutes=3)).isoformat(),'identities':{'codex':self.identity}})
        self.data={'ok':True,'_meta':{'runtimeId':'test'},'result':{'dispatch':{'id':'d','hostScope':{'kind':'local'},'status':'completed','completedAt':(now-timedelta(minutes=1)).isoformat()},'worker':{'dispatchId':'d','state':'succeeded','createdAt':(now-timedelta(minutes=2)).isoformat(),'startOptions':{'launch':{'effective':{'agent':'codex','model':'gpt-6.1-sol','effort':'medium'}}}}}}
        self.identity_patch=patch.object(kit,'tool_identity',return_value=self.identity);self.identity_patch.start();self.addCleanup(self.identity_patch.stop)
    def verify(self,data=None):
        with patch.object(kit,'orca_read',return_value=data or self.data):return kit.verify_profile({},self.state,'standard','d')
    def test_success_repeat_preserves_other_and_time(self):
        kit.write_json(self.state/'model-evidence.json',{'other':{'preserve':True}})
        a=self.verify();b=self.verify()
        self.assertTrue(a['changed']);self.assertFalse(b['changed'])
        self.assertEqual(a['verified_at'],self.data['result']['dispatch']['completedAt'])
        self.assertTrue(kit.read_json(self.state/'model-evidence.json',{})['other']['preserve'])
    def test_reject_non_success_remote_missing_mismatch_old(self):
        variants=[]
        for key,value in [('status','running'),('hostScope',{'kind':'remote'}),('completedAt','2000-01-01T00:00:00Z')]:
            d=copy.deepcopy(self.data);d['result']['dispatch'][key]=value;variants.append(d)
        for key,value in [('state','failed'),('startOptions',{})]:
            d=copy.deepcopy(self.data);d['result']['worker'][key]=value;variants.append(d)
        for key,value in [('agent','claude'),('model','other'),('effort','high')]:
            d=copy.deepcopy(self.data);d['result']['worker']['startOptions']['launch']['effective'][key]=value;variants.append(d)
        for d in variants:
            with self.subTest(d=d),self.assertRaises(ValueError):self.verify(d)
        self.assertFalse((self.state/'model-evidence.json').exists())
    def test_changed_binary_or_late_snapshot(self):
        with patch.object(kit,'tool_identity',return_value=dict(self.identity,size=99)),self.assertRaises(ValueError):self.verify()
        kit.write_json(self.state/'setup-observation.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'identities':{'codex':self.identity}})
        with self.assertRaises(ValueError):self.verify()
    def test_setup_missing_tools_and_no_profile(self):
        with patch.object(kit,'probe',return_value={'available':False}),patch.object(kit,'orca_read',side_effect=ValueError('offline')),patch.object(kit.shutil,'which',return_value=None):
            result=kit.setup(self.root,{},self.state,'claude')
        self.assertFalse(result['checks']['orca_connected']);self.assertFalse(result['checks']['skill_installed'])
        self.assertEqual(result['profiles'],{});self.assertTrue(result['next_steps'])
        self.assertTrue((self.state/'setup-observation.json').exists())
    def test_setup_three_agents(self):
        for agent in ['codex','claude','agy']:
            with patch.object(kit,'probe',return_value={'available':True,'help_ok':True}),patch.object(kit,'orca_read',return_value={'result':{'runtime':{'reachable':True}}}):
                result=kit.setup(self.root,{},self.state,agent)
            self.assertEqual(result['agent'],agent);self.assertIn(agent,result['prompt'])

    def test_embedded_effort_and_remote_environment(self):
        now=datetime.now(timezone.utc)
        kit.write_json(self.state/'setup-observation.json',{'observed_at':(now-timedelta(minutes=3)).isoformat(),'identities':{'agy':self.identity}})
        data=copy.deepcopy(self.data)
        data['result']['worker']['startOptions']['launch']['effective']={'agent':'antigravity','model':'gemini-3.8-flash-low','effort':None}
        with patch.object(kit,'orca_read',return_value=data):
            self.assertEqual(kit.verify_profile({},self.state,'light','d')['status'],'verified')
            data['result']['worker']['startOptions']['launch']['effective']['effort']='high'
            with self.assertRaises(ValueError):kit.verify_profile({},self.state,'light','d')
        with patch.dict(kit.os.environ,{'ORCA_ENVIRONMENT':'remote'}),self.assertRaises(ValueError):self.verify()
