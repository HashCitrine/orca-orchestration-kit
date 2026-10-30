import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import usage

class UsageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.state=Path(self.temp.name)
        self.p={'agent':'codex','model':'test','effort':'high','profile':'deep','status':'ready','explicit':False,'upgrades':0}
    def obs(self,remaining,minutes=300,group='codex',source='manual',agent='codex',account='a',now=1000):
        return usage.observe(self.state,agent,account,group,remaining,minutes,max(10000,now+1000),source,now)
    def test_thresholds_and_windows(self):
        for value,want in [(21,'normal'),(20,'conserve'),(5,'protected'),(0,'protected')]:
            self.obs(value);self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],want)
        self.obs(80);self.obs(4,10080);self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],'protected')
    def test_stale_reset_and_manual_priority(self):
        self.obs(80);self.assertEqual(usage.status(self.state,self.p,{},1301)['state'],'unknown')
        self.assertEqual(usage.status(self.state,self.p,{},10001)['state'],'unknown')
        self.obs(4,source='automatic');self.obs(90,now=1001)
        self.assertEqual(usage.status(self.state,self.p,{},1001)['state'],'protected')
    def test_account_and_group(self):
        self.obs(4);d=usage.load(self.state);d['active']['codex']='b';usage.save(self.state,d)
        self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],'unknown')
        self.obs(90);self.obs(3,group='account')
        self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],'protected')
    def test_restrictive_fresh_window_with_missing_other(self):
        self.obs(90,10080,now=500);self.obs(4)
        self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],'protected')
        self.obs(90);self.assertEqual(usage.status(self.state,self.p,{},1000)['state'],'unknown')
    def test_selection_unknown_explicit_protected_and_separate(self):
        now=usage.time.time();self.obs(4,now=now)
        # Replace reset with a future timestamp for real-time selection.
        d=usage.load(self.state)
        for row in d['records']:row['resets_at']=now+1000
        usage.save(self.state,d)
        config={'usage':{'alternatives':{'design':['review']}}}
        alt={**self.p,'agent':'agy','profile':'review'}
        self.assertEqual(usage.select(self.p,config,self.state,'design',lambda n:alt)['status'],'blocked')
        usage.observe(self.state,'agy','b','account',80,300,now+1000)
        selected=usage.select(self.p,config,self.state,'design',lambda n:alt)
        self.assertEqual(selected['profile'],'review')
        self.assertEqual(usage.select({**self.p,'explicit':True},config,self.state,'design',lambda n:alt)['status'],'blocked')
        self.assertEqual(usage.select(self.p,config,self.state,'design',lambda n:{**alt,'effort':'low'})['status'],'blocked')
        self.assertEqual(usage.select(self.p,{'usage':{'enabled':False}},self.state,'design',lambda n:alt)['status'],'ready')
    def test_refresh_parse_failure_account_change(self):
        response={'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':30,'windowDurationMins':300,'resetsAt':9999999999},'secondary':{'usedPercent':90,'windowDurationMins':10080,'resetsAt':9999999999}}}}
        with patch.object(usage,'codex_read',return_value=('hash-a',response)):
            self.assertEqual(usage.refresh(self.state,{})['status'],'updated')
        self.assertEqual(len(usage.load(self.state)['records']),2)
        with patch.object(usage,'codex_read',side_effect=ValueError('failed')):usage.refresh(self.state,{})
        self.assertNotIn('codex',usage.load(self.state)['active'])
        self.assertEqual(usage.status(self.state,self.p,{})['state'],'unknown')
    def test_input_validation(self):
        for value in [-1,101,float('nan')]:
            with self.assertRaises(ValueError):self.obs(value)
        with self.assertRaises(ValueError):usage.policy({'usage':{'protect_percent':25}})
