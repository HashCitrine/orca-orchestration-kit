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
    def orca_payload(self,now,claude_status='ok'):
        ms=lambda t:t*1000
        return {'ok':True,'result':{'claude':{'activeAccountId':None},'rateLimits':{
            'claudeTarget':{'runtime':'host'},
            'claude':{'status':claude_status,'error':None if claude_status=='ok' else 'failed','updatedAt':ms(now-30),
                      'session':{'usedPercent':20,'windowMinutes':300,'resetsAt':ms(now+3600)},
                      'weekly':{'usedPercent':85,'windowMinutes':10080,'resetsAt':ms(now+86400)},'fableWeekly':None},
            'antigravity':{'status':'ok','error':None,'updatedAt':ms(now-60),'buckets':[
                {'group':'Gemini Models','usedPercent':10,'windowMinutes':300,'resetsAt':ms(now+3600)},
                {'group':'Gemini Models','usedPercent':30,'windowMinutes':10080,'resetsAt':ms(now+86400)},
                {'group':'Gemini 4 Argon','usedPercent':70,'windowMinutes':10080,'resetsAt':ms(now+86400)}]}}}}
    def test_orca_claude_and_agy(self):
        now=usage.time.time();payload=self.orca_payload(now)
        claude=usage.refresh(self.state,{},'claude',lambda:payload)
        self.assertEqual(claude['status'],'updated');self.assertEqual(len(claude['windows']),2)
        self.assertEqual({w['remaining_percent'] for w in claude['windows']},{80,15})
        self.assertAlmostEqual(claude['windows'][0]['observed_at'],now-30)
        self.assertAlmostEqual(claude['windows'][0]['resets_at'],now+3600)
        self.assertEqual(usage.load(self.state)['active']['claude'],'orca:system:host')
        q=usage.status(self.state,{**self.p,'agent':'claude'},{})
        self.assertEqual((q['state'],q['remaining_percent']),('conserve',15))
        usage.refresh(self.state,{},'agy',lambda:payload)
        light=usage.status(self.state,{'agent':'agy','quota_groups':['Gemini Models']},{})
        review=usage.status(self.state,{'agent':'agy','quota_groups':['Gemini Models','Gemini 4 Argon']},{})
        self.assertEqual((light['state'],light['remaining_percent']),('normal',70))
        self.assertEqual((review['state'],review['remaining_percent']),('normal',30))
        self.assertEqual(usage.status(self.state,{'agent':'agy'},{})['state'],'unknown')
        self.assertEqual(usage.status(self.state,{**self.p,'agent':'claude'},{},now+400)['state'],'unknown')
    def test_orca_failure_isolated(self):
        now=usage.time.time()
        usage.refresh(self.state,{},'claude',lambda:self.orca_payload(now))
        usage.refresh(self.state,{},'agy',lambda:self.orca_payload(now))
        failed=usage.refresh(self.state,{},'claude',lambda:self.orca_payload(now,'error'))
        self.assertEqual(failed['status'],'unknown');d=usage.load(self.state)
        self.assertNotIn('claude',d['active']);self.assertEqual(d['active']['agy'],'orca:antigravity')
        self.assertEqual(usage.status(self.state,{**self.p,'agent':'claude'},{})['state'],'unknown')
        self.assertEqual(usage.refresh(self.state,{},'agy')['status'],'unknown')
    def test_orca_alternative_selected(self):
        now=usage.time.time();self.obs(10,now=now)
        d=usage.load(self.state)
        for row in d['records']:row['resets_at']=now+1000
        usage.save(self.state,d);usage.refresh(self.state,{},'agy',lambda:self.orca_payload(now))
        alt={**self.p,'agent':'agy','profile':'review','quota_groups':['Gemini Models','Gemini 4 Argon']}
        selected=usage.select(self.p,{'usage':{'alternatives':{'design':['review']}}},self.state,'design',lambda n:alt)
        self.assertEqual((selected['profile'],selected['usage']['state']),('review','normal'))
    def test_input_validation(self):
        for value in [-1,101,float('nan')]:
            with self.assertRaises(ValueError):self.obs(value)
        with self.assertRaises(ValueError):usage.policy({'usage':{'protect_percent':25}})
