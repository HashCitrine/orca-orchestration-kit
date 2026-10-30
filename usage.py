"""Local quota observations, read-only Codex App Server and Orca rate limit adapters."""
import hashlib
import json
import math
import queue
import subprocess
import threading
import time
from pathlib import Path


AUTOMATIC=('automatic','orca')
DEFAULT_GROUPS={'codex':['codex'],'claude':['claude']}


def load(state):
    p=state/'usage.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'active':{},'records':[]}


def save(state,data):
    state.mkdir(parents=True,exist_ok=True)
    p=state/'usage.json';tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');tmp.replace(p)


def policy(config):
    p={'enabled':True,'ttl_seconds':300,'conserve_percent':20,'protect_percent':5,'alternatives':{}}
    supplied=config.get('usage',{})
    if not isinstance(supplied,dict) or set(supplied)-set(p):raise ValueError('invalid usage settings')
    p.update(supplied)
    if type(p['enabled']) is not bool:raise ValueError('usage.enabled must be boolean')
    for k in ['ttl_seconds','conserve_percent','protect_percent']:
        if type(p[k]) not in (int,float) or not math.isfinite(p[k]):raise ValueError('invalid usage threshold')
    if not 0<=p['protect_percent']<p['conserve_percent']<=100 or p['ttl_seconds']<=0:raise ValueError('invalid usage thresholds')
    if not isinstance(p['alternatives'],dict) or any(not isinstance(v,list) or any(not isinstance(x,str) for x in v) for v in p['alternatives'].values()):raise ValueError('invalid usage alternatives')
    return p


def observe(state,agent,account,group,remaining,minutes,reset,source='manual',now=None):
    now=time.time() if now is None else now
    if (not account or not group or not math.isfinite(remaining) or not 0<=remaining<=100
            or minutes<=0 or not math.isfinite(reset) or reset<=now):raise ValueError('invalid quota observation')
    d=load(state);d['active'][agent]=account
    row={'agent':agent,'account':account,'group':group,'remaining_percent':remaining,
         'window_minutes':minutes,'resets_at':reset,'observed_at':now,'source':source}
    d['records']=[r for r in d['records'] if not (r['agent']==agent and r['account']==account and r['group']==group and r['window_minutes']==minutes and r['source']==source)]+[row]
    save(state,d);return row


def status(state,profile,config,now=None):
    now=time.time() if now is None else now;p=policy(config)
    if not p['enabled']:return {'state':'disabled','windows':[]}
    d=load(state);agent=profile['agent'];account=d['active'].get(agent)
    # AGY model groups are never guessed; its profiles must name quota_groups.
    groups=profile.get('quota_groups', DEFAULT_GROUPS.get(agent,[]))
    applicable=set(groups)|{'account'};windows=[]
    rows=[r for r in d['records'] if r['agent']==agent and r['account']==account and r['group'] in applicable]
    for key in {(r['group'],r['window_minutes']) for r in rows}:
        eligible=[r for r in rows if (r['group'],r['window_minutes'])==key and 0<=now-r['observed_at']<=p['ttl_seconds'] and r['resets_at']>now]
        if eligible:windows.append(max(eligible,key=lambda r:(r['source'] in AUTOMATIC,r['observed_at'])))
    covered={r['group'] for r in windows}
    if not windows:return {'state':'unknown','windows':[],'reason':'missing, stale, reset or account unknown'}
    minimum=min(r['remaining_percent'] for r in windows)
    level='protected' if minimum<=p['protect_percent'] else 'conserve' if minimum<=p['conserve_percent'] else 'normal'
    # Missing related windows cannot turn a known restriction into spare quota.
    complete=all(g in covered for g in groups) and all(any((x['group'],x['window_minutes'])==(r['group'],r['window_minutes']) for x in windows) for r in rows)
    if level=='normal' and not complete:level='unknown'
    return {'state':level,'remaining_percent':minimum,'windows':windows,'complete':complete}


def codex_read(executable):
    process=subprocess.Popen([executable,'app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL,text=True,encoding='utf-8',bufsize=1)
    messages=queue.Queue()
    def reader():
        for line in process.stdout:
            try:messages.put(json.loads(line))
            except ValueError:pass
        messages.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def send(v):process.stdin.write(json.dumps(v)+'\n');process.stdin.flush()
    def request(i,method,params=None):
        send({'id':i,'method':method,**({'params':params} if params is not None else {})})
        deadline=time.monotonic()+15
        while True:
            try:v=messages.get(timeout=max(.01,deadline-time.monotonic()))
            except queue.Empty:raise ValueError('Codex usage request timed out') from None
            if v is None:raise ValueError('Codex usage connection closed')
            if v.get('id')==i:
                if 'error' in v:raise ValueError('Codex usage request unsupported or unauthorized')
                return v.get('result',{})
            if time.monotonic()>deadline:raise ValueError('Codex usage request timed out')
    try:
        request(1,'initialize',{'clientInfo':{'name':'orca_quota','version':'1.0'},'capabilities':{}})
        send({'method':'initialized'})
        a=request(2,'account/read',{'refreshToken':False}).get('account')
        if not isinstance(a,dict) or not (a.get('id') or a.get('accountId') or a.get('email')):raise ValueError('Codex account identity unavailable')
        identity=hashlib.sha256(str(a.get('id') or a.get('accountId') or a['email']).encode()).hexdigest()[:24]
        limits=request(3,'account/rateLimits/read')
        b=request(4,'account/read',{'refreshToken':False}).get('account')
        if a!=b:raise ValueError('Codex account changed during refresh')
        return identity,limits
    finally:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        process.stdin.close();process.stdout.close()


def orca_window(agent,account,group,window,updated):
    used=float(window['usedPercent']);minutes=int(window['windowMinutes']);reset=float(window['resetsAt'])/1000
    if not math.isfinite(used) or not 0<=used<=100 or minutes<=0 or not math.isfinite(reset):raise ValueError('invalid provider quota')
    return {'agent':agent,'account':account,'group':group,'remaining_percent':100-used,'window_minutes':minutes,
            'resets_at':reset,'observed_at':updated,'source':'orca'}


def orca_records(payload,agent):
    # Orca reports the account it launches workers with; observed_at is Orca's own refresh time.
    limits=payload['result']['rateLimits']
    entry=limits['claude' if agent=='claude' else 'antigravity']
    if not isinstance(entry,dict) or entry.get('status')!='ok' or entry.get('error'):raise ValueError('Orca quota unavailable')
    updated=float(entry['updatedAt'])/1000
    if not math.isfinite(updated):raise ValueError('invalid provider quota')
    if agent=='claude':
        active=payload['result'].get('claude',{}).get('activeAccountId') or 'system'
        account='orca:'+str(active)+':'+str((limits.get('claudeTarget') or {}).get('runtime','host'))
        windows=[('claude',entry.get(k)) for k in ('session','weekly')]+[('claude-fable',entry.get('fableWeekly'))]
    else:
        account='orca:antigravity'
        windows=[(b['group'],b) for b in entry['buckets']]
    return account,[orca_window(agent,account,group,w,updated) for group,w in windows if w is not None]


def refresh(state,config,agent='codex',orca_reader=None):
    if agent not in ('codex','claude','agy'):return {'status':'unknown','agent':agent,'reason':'automatic adapter unavailable; use manual input'}
    try:
        if agent!='codex':
            if orca_reader is None:raise ValueError('Orca reader unavailable')
            account,records=orca_records(orca_reader(),agent)
            d=load(state);d['active'][agent]=account
            d['records']=[r for r in d['records'] if not(r['agent']==agent and r['source'] in AUTOMATIC)]+records
            save(state,d)
            return {'status':'updated' if records else 'unknown','agent':agent,'source':'orca','windows':records}
        account,response=codex_read(config.get('executables',{}).get('codex','codex'))
        buckets=response.get('rateLimitsByLimitId')
        if not isinstance(buckets,dict) or not buckets:
            single=response.get('rateLimits');buckets={single.get('limitId') or 'codex':single} if isinstance(single,dict) else {}
        # Parse completely before publishing a new account observation.
        now=time.time();records=[]
        for group,bucket in buckets.items():
            for field in ['primary','secondary']:
                w=bucket.get(field)
                if w is None:continue
                used=float(w['usedPercent']);minutes=int(w['windowDurationMins']);reset=float(w['resetsAt'])
                if not math.isfinite(used) or not 0<=used<=100 or minutes<=0 or not math.isfinite(reset):raise ValueError('invalid provider quota')
                records.append({'agent':agent,'account':account,'group':group,'remaining_percent':100-used,'window_minutes':minutes,'resets_at':reset,'observed_at':now,'source':'automatic'})
        d=load(state);d['active'][agent]=account
        d['records']=[r for r in d['records'] if not(r['agent']==agent and r['source'] in AUTOMATIC)]+records
        save(state,d)
        return {'status':'updated' if records else 'unknown','agent':agent,'windows':records}
    except (OSError,ValueError,KeyError,TypeError,OverflowError):
        # Identity may have changed; never reuse an old account after refresh failure.
        d=load(state);d['active'].pop(agent,None);save(state,d)
        return {'status':'unknown','agent':agent,'reason':'refresh failed; previous account observations not used'}


def select(base,config,state,task_type,resolve):
    if base.get('status')!='ready':return base
    p=policy(config);q=status(state,base,config)
    base={**base,'usage':q,'baseline_profile':base['profile']}
    if q['state'] not in ('conserve','protected'):return base
    if not base.get('explicit'):
        for name in p['alternatives'].get(task_type,[]):
            alternative=resolve(name)
            if alternative.get('status')!='ready' or alternative['effort'] not in ('low','medium','high'):continue
            if task_type!='simple' and {'low':0,'medium':1,'high':2}.get(alternative['effort'],-1)<{'low':0,'medium':1,'high':2}.get(base['effort'],99):continue
            other=status(state,alternative,config)
            old={(w['agent'],w['account'],w['group']) for w in q['windows']}
            new={(w['agent'],w['account'],w['group']) for w in other['windows']}
            if other['state']=='normal' and not old.intersection(new):
                return {**alternative,'explicit':False,'upgrades':base['upgrades'],'usage':other,
                        'baseline_profile':base['profile'],'usage_reason':'quality-approved alternative with confirmed separate quota'}
    if q['state']=='protected':return {**base,'status':'blocked','launch_args':[], 'usage_reason':'quota reserve protected; select another profile or wait for reset'}
    return {**base,'usage_reason':'low quota; no confirmed quality-approved alternative; retaining profile'}
