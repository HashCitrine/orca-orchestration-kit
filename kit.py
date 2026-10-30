#!/usr/bin/env python3
"""Portable, conservative installer for Orca team skills (Python 3.9+)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import usage

NAME = 'orca-team'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)

def roots(home, config):
    values = {'codex': Path(os.environ.get('CODEX_HOME', str(home/'.codex')))/'skills',
              'claude': home/'.claude/skills', 'agy': home/'.gemini/config/skills'}
    for key, value in config.get('skill_roots', {}).items():
        if key not in values:
            raise ValueError('unknown skill root: '+key)
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError('skill roots must be absolute')
        values[key] = path
    return values

def orca_command(system=None, env=None):
    env = os.environ if env is None else env
    system = platform.system() if system is None else system
    if env.get('ORCA_CLI_COMMAND'):
        return env['ORCA_CLI_COMMAND']
    if env.get('ORCA_DEV_REPO_ROOT'):
        return 'orca-dev'
    return 'orca-ide' if system == 'Linux' else 'orca'

def safe_path(path):
    return not any(p.is_symlink() for p in [path, *path.parents])

def claude_settings_path(home, env=None):
    env = os.environ if env is None else env
    base = Path(env['CLAUDE_CONFIG_DIR']).expanduser() if env.get('CLAUDE_CONFIG_DIR') else home/'.claude'
    return base/'settings.json'

def orca_data_root(home, system=None, env=None):
    env = os.environ if env is None else env
    system = platform.system() if system is None else system
    if system == 'Darwin':
        return home/'Library/Application Support/orca'
    if system == 'Windows':
        return Path(env['APPDATA'])/'orca' if env.get('APPDATA') else home/'AppData/Roaming/orca'
    return Path(env['XDG_CONFIG_HOME'])/'orca' if env.get('XDG_CONFIG_HOME') else home/'.config/orca'

def orca_claude_args(home, system=None, env=None):
    # Read-only: Orca owns this file. Unknown layouts yield None instead of an error.
    found = []
    for path in sorted(orca_data_root(home, system, env).glob('profiles/*/orca-data.json')):
        try:
            value = json.loads(path.read_text(encoding='utf-8'))['settings']['agentDefaultArgs']['claude']
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if isinstance(value, str):
            found.append(value)
    return found or None

def claude_readiness(home, system=None, env=None):
    args = orca_claude_args(home, system, env)
    settings = claude_settings_path(home, env)
    try:
        accepted = read_json(settings, {}).get('skipDangerousModePermissionPrompt') is True
    except (OSError, ValueError, AttributeError):
        accepted = False
    if args is None:
        return {'status': 'unknown', 'reason': 'Orca agent arguments not found; verify with a small worker task'}
    bypass = any('--dangerously-skip-permissions' in a or 'bypassPermissions' in a for a in args)
    if bypass and not accepted:
        return {'status': 'needs_claude_setup', 'orca_args': args,
                'reason': 'Claude waits on the bypass-permissions confirmation screen',
                'action': 'run: python3 kit.py claude-setup'}
    return {'status': 'ready', 'orca_args': args, 'bypass_confirmation_skipped': accepted}

def claude_setup(home, env=None):
    path = claude_settings_path(home, env)
    if not safe_path(path):
        raise ValueError('symlink conflict: '+str(path))
    original = path.read_bytes() if path.exists() else None
    settings = json.loads(original.decode('utf-8')) if original is not None else {}
    if not isinstance(settings, dict):
        raise ValueError('Claude settings must be a JSON object: '+str(path))
    if settings.get('skipDangerousModePermissionPrompt') is True:
        return {'changed': False, 'settings': str(path)}
    backup = None
    if original is not None:
        backup = path.with_name(path.name+'.orca-team-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        if backup.exists():
            raise ValueError('backup path exists: '+str(backup))
        backup.write_bytes(original)
    settings['skipDangerousModePermissionPrompt'] = True
    write_json(path, settings)
    return {'changed': True, 'settings': str(path), 'backup': str(backup) if backup else None,
            'revert': 'delete skipDangerousModePermissionPrompt from the settings file'}

def install(source, destinations, state, remove=False):
    manifest_path = state/'manifest.json'
    old = read_json(manifest_path, {})
    desired = {} if remove else {str(root/NAME/p.relative_to(source)): p.read_bytes()
                                 for root in destinations.values()
                                 for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    # Preflight every file before any mutation. Existing unowned files are never adopted.
    for name in set(old) | set(desired):
        path = Path(name)
        if not safe_path(path):
            raise ValueError('symlink conflict: '+name)
        if path.exists() and (not path.is_file() or name not in old or digest(path.read_bytes()) != old[name]):
            raise ValueError('user file conflict, preserved: '+name)
    for name in old.keys() - desired.keys():
        Path(name).unlink(missing_ok=True)
    for name, data in desired.items():
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name+'.orca-team-tmp')
        if temporary.exists() or temporary.is_symlink():
            raise ValueError('temporary path conflict: '+str(temporary))
        temporary.write_bytes(data)
        temporary.replace(path)
    write_json(manifest_path, {n: digest(d) for n, d in desired.items()})
    return {'managed_files': len(desired), 'removed_files': len(old.keys()-desired.keys())}

def probe(command):
    executable = shutil.which(command)
    if not executable:
        return {'available': False}
    try:
        p = subprocess.run([executable, '--help'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=15, shell=False)
        return {'available': True, 'path': executable, 'help_ok': p.returncode == 0,
                'binary_mtime_ns': Path(executable).stat().st_mtime_ns,
                'binary_size': Path(executable).stat().st_size,
                'interface_hash': digest(p.stdout.encode())}
    except (OSError, subprocess.TimeoutExpired):
        return {'available': True, 'path': executable, 'help_ok': False}

def doctor(home, config, state):
    commands = {'orca': orca_command(), 'claude':'claude', 'codex':'codex', 'agy':'agy'}
    commands.update(config.get('executables', {}))
    observations = {k: probe(v) for k,v in commands.items()}
    claude_worker = claude_readiness(home)
    fingerprint = digest(json.dumps({'config':config,'tools':observations,'claude_worker':claude_worker},
                                    sort_keys=True).encode())
    previous = read_json(state/'capabilities.json', {})
    report = {'platform': platform.system(), 'tools': observations,
              'changed': previous.get('fingerprint') != fingerprint,
              'fingerprint': fingerprint, 'models': config.get('models', {}),
              'model_verification': 'runtime preflight required; defaults inherited',
              'claude_worker': claude_worker,
              'skill_roots': {k:str(v) for k,v in roots(home,config).items()}}
    write_json(state/'capabilities.json',report)
    return report


def routing_defaults():
    base = Path(__file__).resolve().parent
    path = base/'routing.json'
    if not path.exists():
        path = base/'skills'/NAME/'scripts/routing.json'
    return read_json(path, {})


def routing_config(config):
    default = routing_defaults()
    if not isinstance(config.get('profiles', {}), dict) or not isinstance(config.get('routes', {}), dict):
        raise ValueError('profiles and routes must be objects')
    profiles = dict(default['profiles'])
    # Override whole profiles to avoid retaining a different model's effort encoding.
    profiles.update(config.get('profiles', {}))
    routes = dict(default['routes'])
    routes.update(config.get('routes', {}))
    if not isinstance(config.get('profiles', {}), dict) or not isinstance(config.get('routes', {}), dict):
        raise ValueError('profiles and routes must be objects')
    for name, p in profiles.items():
        if not isinstance(p, dict) or set(p)-{'agent','model','effort','effort_mode','fallback','upgrade','quota_groups'}:
            raise ValueError('invalid profile: '+name)
        if p.get('agent') not in ('codex','claude','agy') or not isinstance(p.get('model'),str) or not p['model'].strip():
            raise ValueError('profile requires agent and model: '+name)
        if p.get('effort') not in ('low','medium','high','xhigh','max','ultra') or p.get('effort_mode') not in ('flag','embedded'):
            raise ValueError('invalid effort or effort_mode: '+name)
        if p['effort_mode']=='embedded' and not p['model'].endswith('-'+p['effort']):
            raise ValueError('embedded effort conflicts with model: '+name)
        if 'quota_groups' in p and (not isinstance(p['quota_groups'],list) or any(not isinstance(g,str) or not g for g in p['quota_groups'])):
            raise ValueError('invalid quota_groups')
        for edge in ('fallback','upgrade'):
            if p.get(edge) and p[edge] not in profiles:
                raise ValueError('unknown '+edge+' profile: '+name)
    if any(v not in profiles for v in routes.values()):
        raise ValueError('route references unknown profile')
    for start in profiles:
        seen=set();current=start
        while current:
            if current in seen:
                raise ValueError('fallback cycle: '+start)
            seen.add(current);current=profiles[current].get('fallback')
    return profiles,routes


def profile_key(p):
    return '|'.join(p[k] for k in ('agent','model','effort','effort_mode'))


def tool_identity(agent, config):
    executable=shutil.which(config.get('executables',{}).get(agent,agent))
    if not executable:
        return None
    stat=Path(executable).stat()
    return {'path':executable,'mtime_ns':stat.st_mtime_ns,'size':stat.st_size}


def route_base(config, state, task_type, complexity='normal', profile=None, model=None,
          effort=None, agent=None, prior=None, failure=None, settled=False, implementation_agent=None):
    profiles,routes=routing_config(config)
    explicit=bool(profile or model or effort or agent)
    selected=profile or ('deep' if complexity=='complex' and task_type!='review' else routes.get(task_type))
    if selected not in profiles:
        raise ValueError('unknown task type/profile')
    if prior:
        if failure!='quality' or not settled or prior.get('upgrades',0)>=1 or prior.get('explicit'):
            return {'status':'blocked','reason':'upgrade requires settled quality failure, no prior upgrade, and no explicit override'}
        selected=profiles.get(prior.get('profile'),{}).get('upgrade')
        if not selected:
            return {'status':'blocked','reason':'no approved upgrade'}
    evidence=read_json(state/'model-evidence.json',{})
    rejected=[];seen=set()
    while selected and selected not in seen:
        seen.add(selected);p=dict(profiles[selected])
        for key,value in [('agent',agent),('model',model),('effort',effort)]:
            if value:p[key]=value
        # Revalidate explicit overrides as complete profile definitions.
        routing_config({'profiles':{'override':p}})
        reason=None
        if not explicit and p['effort'] not in ('low','medium','high'):
            reason='automatic effort exceeds high'
        record=evidence.get(profile_key(p),{})
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(record['verified_at'])).total_seconds()
            fresh=0 <= age <= 7*86400
        except (KeyError,ValueError,TypeError):
            fresh=False
        if not reason and (not fresh or tool_identity(p['agent'],config) is None or record.get('identity')!=tool_identity(p['agent'],config) or not record.get('dispatch_id')):
            reason='missing, stale, or changed-runtime smoke-test evidence'
        if reason:
            rejected.append({'profile':selected,'reason':reason})
            if explicit or prior:break
            selected=p.get('fallback');continue
        argv=['--agent',{'agy':'antigravity'}.get(p['agent'],p['agent']),'--model',p['model']]
        if p['effort_mode']=='flag':argv+=['--effort',p['effort']]
        return {'status':'ready','profile':selected,**p,'launch_args':argv,
                'reason':task_type+'/'+complexity,'rejected':rejected,'explicit':explicit,
                'upgrades':1 if prior else 0,'actual_model':'unverified until launch receipt/provider response',
                'review_independence': None if task_type!='review' else p['agent']!=implementation_agent}
    return {'status':'blocked','reason':'no verified compatible profile','rejected':rejected}



def route(config, state, task_type, complexity='normal', profile=None, model=None,
          effort=None, agent=None, prior=None, failure=None, settled=False, implementation_agent=None):
    base=route_base(config,state,task_type,complexity,profile,model,effort,agent,prior,failure,settled,implementation_agent)
    return usage.select(base,config,state,task_type,
                        lambda name:route_base(config,state,task_type,complexity,profile=name,implementation_agent=implementation_agent))


def orca_read(config, *args):
    executable=config.get('executables',{}).get('orca',orca_command())
    try:
        result=subprocess.run([executable,*args,'--json'],capture_output=True,text=True,
                              encoding='utf-8',errors='replace',timeout=20,shell=False)
    except (OSError,subprocess.TimeoutExpired):
        raise ValueError('Orca 연결 실패: 앱 실행과 CLI 경로를 확인하세요.') from None
    try:
        payload=json.loads(result.stdout)
    except ValueError:
        raise ValueError('Orca 응답 형식을 확인할 수 없습니다.') from None
    if result.returncode or not isinstance(payload,dict) or payload.get('ok') is not True:
        raise ValueError('Orca 요청 실패: 런타임 연결·권한·명령 지원 여부를 확인하세요.')
    return payload


def setup(home, config, state, agent):
    profiles,_=routing_config(config)
    executable=config.get('executables',{}).get(agent,agent)
    cli=probe(executable)
    installed=(roots(home,config)[agent]/NAME/'SKILL.md').is_file()
    try:
        result=orca_read(config,'status')['result']
        connected=result.get('runtime',{}).get('reachable') is True
    except (ValueError,KeyError,TypeError):
        connected=False
    checks={'python':sys.version.split()[0],'git':bool(shutil.which('git')),
            'orca_connected':connected,'agent_cli':bool(cli.get('available') and cli.get('help_ok')),
            'skill_installed':installed}
    candidates={name:route(config,state,'implementation',profile=name)['status']
                for name,p in profiles.items() if p['agent']==agent}
    next_steps=[]
    if not checks['git']:next_steps.append('일반 터미널: Git을 설치하고 git --version을 확인하세요.')
    if not connected:next_steps.append('Orca 앱을 실행하고 해당 환경의 Orca CLI 연결을 확인하세요.')
    if not checks['agent_cli']:next_steps.append(agent+' CLI를 공식 안내로 설치하고 새 터미널에서 실행해 로그인하세요.')
    if not installed:next_steps.append('키트 저장소: python3 kit.py install (Windows: py -3 kit.py install)')
    if not candidates:next_steps.append('이 도구의 기본 프로필이 없습니다. 에이전트에게 지원 모델·effort를 확인하고 로컬 profiles에 전체 프로필을 추가하도록 요청하세요.')
    elif any(v!='ready' for v in candidates.values()):next_steps.append('Orca의 새 에이전트 대화에서 아래 요청문으로 작은 모델 검증을 진행하세요.')
    if not next_steps:next_steps.append('Orca에서 작업할 프로젝트를 열고 새 대화에서 orca-team을 호출하세요.')
    identities={a:tool_identity(a,config) for a in ('codex','claude','agy')}
    write_json(state/'setup-observation.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'identities':identities})
    return {'agent':agent,'checks':checks,'profiles':candidates,'next_steps':next_steps,
            'authentication':'CLI 존재만 확인했습니다. 각 도구에서 로그인 여부를 확인하세요.',
            'prompt':'orca-team 스킬을 읽고 '+agent+'로 첫 읽기 전용 작업을 준비해줘. 사용할 프로필이 없으면 지원 모델과 effort를 확인해 로컬 프로필을 구성해줘. setup을 다시 실행한 뒤 현재 Orca 작업 공간에서 작은 검증 작업을 실행하고, 성공한 Dispatch를 verify-profile로 등록해줘. 완료 보고 처리와 작업자 회수까지 진행하고 결과를 알려줘.'}


def parse_time(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def verify_profile(config,state,name,dispatch_id):
    if os.environ.get('ORCA_ENVIRONMENT') or os.environ.get('ORCA_PAIRING_CODE'):
        raise ValueError('원격 Orca 환경의 검증 등록은 지원하지 않습니다.')
    profiles,_=routing_config(config)
    if name not in profiles:raise ValueError('알 수 없는 프로필입니다.')
    p=profiles[name]
    # Query the live runtime, never accept caller-provided completion JSON.
    payload=orca_read(config,'orchestration','worker-show','--dispatch',dispatch_id)
    try:
        result=payload['result'];dispatch=result['dispatch'];worker=result['worker']
        if dispatch['id']!=dispatch_id or worker['dispatchId']!=dispatch_id:
            raise ValueError('Dispatch ID 불일치')
        if dispatch['hostScope']['kind']!='local':raise ValueError('로컬 검증만 지원합니다.')
        if dispatch['status']!='completed' or worker['state']!='succeeded':
            raise ValueError('성공한 완료 작업만 등록할 수 있습니다.')
        effective=worker['startOptions']['launch']['effective']
        expected_agent={'agy':'antigravity'}.get(p['agent'],p['agent'])
        expected_effort=p['effort'] if p['effort_mode']=='flag' else None
        if (effective['agent'],effective['model'],effective.get('effort'))!=(expected_agent,p['model'],expected_effort):
            raise ValueError('실제 도구·모델·effort가 프로필과 다릅니다.')
        completed=parse_time(dispatch['completedAt']);started=parse_time(worker['createdAt'])
        age=(datetime.now(timezone.utc)-completed).total_seconds()
        if not 0<=age<=7*86400 or completed<started:raise ValueError('완료 시각이 유효하지 않거나 7일이 지났습니다.')
        observation=read_json(state/'setup-observation.json',{})
        identity=tool_identity(p['agent'],config)
        if (not identity or observation['identities'][p['agent']]!=identity
                or parse_time(observation['observed_at'])>started
                or identity['mtime_ns']/1e9>started.timestamp()):
            raise ValueError('작업 전 setup 기록과 현재 실행 파일이 일치해야 합니다. setup 후 새 검증 작업을 실행하세요.')
    except (KeyError,TypeError,AttributeError):
        raise ValueError('검증 필드 또는 작업 전 setup 기록이 없습니다. 등록하지 않았습니다.') from None
    record={'verified_at':completed.isoformat(),'identity':identity,'dispatch_id':dispatch_id,
            'source':'Orca worker-show: succeeded + launch.effective','actual_model':effective['model'],
            'actual_effort':p['effort'],'runtime_id':payload.get('_meta',{}).get('runtimeId')}
    path=state/'model-evidence.json';evidence=read_json(path,{})
    if not isinstance(evidence,dict):raise ValueError('검증 파일이 JSON 객체가 아닙니다.')
    key=profile_key(p);changed=evidence.get(key)!=record
    if changed:
        evidence[key]=record;write_json(path,evidence)
    return {'status':'verified','profile':name,'changed':changed,'verified_at':record['verified_at'],
            'dispatch_id':dispatch_id,'next_step':'조정자가 완료 메시지를 처리하고 작업자를 회수하세요.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install','update','uninstall','doctor','claude-setup','route','setup','verify-profile','usage'])
    parser.add_argument('--home',type=Path,default=Path.home(),help='isolated installation home for tests')
    parser.add_argument('--task-type', choices=['simple','implementation','test','design','debug','review'])
    parser.add_argument('--complexity', choices=['normal','complex'], default='normal')
    parser.add_argument('--profile')
    parser.add_argument('--model')
    parser.add_argument('--effort')
    parser.add_argument('--agent', choices=['codex','claude','agy'])
    parser.add_argument('--prior', type=Path, help='previous route JSON for a quality-failure upgrade')
    parser.add_argument('--failure', choices=['quality','auth','network','installation'])
    parser.add_argument('--settled', action='store_true', help='coordinator has verified prior Dispatch settlement')
    parser.add_argument('--implementation-agent', choices=['codex','claude','agy'])
    parser.add_argument('usage_action',nargs='?',choices=['refresh','show','set'])
    parser.add_argument('--account',help='local non-personal account label for manual input')
    parser.add_argument('--group')
    parser.add_argument('--remaining',type=float)
    parser.add_argument('--window-minutes',type=int)
    parser.add_argument('--resets-at',type=float,help='Unix timestamp in seconds')
    parser.add_argument('--dispatch')
    parser.add_argument('--json',action='store_true',help='machine-readable setup report')
    args=parser.parse_args()
    state=args.home/'.config/orca-orchestration-kit'
    try:
        config=read_json(state/'config.json',{})
        if not isinstance(config,dict) or set(config)-{'executables','skill_roots','models','efforts','max_workers','profiles','routes','usage'}:
            raise ValueError('unsupported configuration keys')
        if type(config.get('max_workers',2)) is not int or config.get('max_workers',2) not in (1,2):
            raise ValueError('max_workers must be 1 or 2')
        for section in ('executables','skill_roots','models','efforts'):
            values=config.get(section,{})
            if not isinstance(values,dict) or any(not isinstance(v,str) or not v.strip() for v in values.values()):
                raise ValueError(section+' must map names to nonempty strings')
            allowed={'codex','claude','agy'}|({'orca'} if section=='executables' else set())
            if set(values)-allowed:
                raise ValueError('unknown agent in '+section)
        for agent in config.get('efforts',{}):
            if agent not in config.get('models',{}):
                raise ValueError('effort requires an explicit model')
        profiles,_=routing_config(config)
        usage_policy=usage.policy(config)
        if any(name not in profiles for names in usage_policy['alternatives'].values() for name in names):
            raise ValueError('unknown usage alternative profile')
        if args.command=='usage':
            if args.usage_action=='refresh':result=usage.refresh(state,config,args.agent or 'codex')
            elif args.usage_action=='show':
                result={'profiles':{name:usage.status(state,p,config) for name,p in profiles.items()}}
            elif args.usage_action=='set':
                if not args.agent or not args.account or not args.group or any(v is None for v in [args.remaining,args.window_minutes,args.resets_at]):
                    raise ValueError('set requires --agent --account --group --remaining --window-minutes --resets-at')
                result=usage.observe(state,args.agent,args.account,args.group,args.remaining,args.window_minutes,args.resets_at)
            else:raise ValueError('usage requires refresh, show or set')
        elif args.command=='setup':
            if not args.agent:raise ValueError('--agent required')
            result=setup(args.home,config,state,args.agent)
        elif args.command=='verify-profile':
            if not args.profile or not args.dispatch:raise ValueError('--profile and --dispatch required')
            result=verify_profile(config,state,args.profile,args.dispatch)
        elif args.command=='route':
            if not args.task_type:
                raise ValueError('--task-type required')
            result=route(config,state,args.task_type,args.complexity,args.profile,args.model,args.effort,
                         args.agent,read_json(args.prior,{}) if args.prior else None,args.failure,
                         args.settled,args.implementation_agent)
        elif args.command=='doctor':
            result=doctor(args.home,config,state)
        elif args.command=='claude-setup':
            result=claude_setup(args.home)
        else:
            source=Path(__file__).resolve().parent/'skills'/NAME
            if args.command!='uninstall' and not (source/'SKILL.md').is_file():
                raise ValueError('install/update must run from repository root kit.py')
            result=install(source,roots(args.home,config),state,args.command=='uninstall')
        if args.command=='usage' and not args.json:
            print('사용량: '+str(result.get('status',result.get('source','profile summary'))))
            if 'reason' in result:print(result['reason'])
            for name,entry in result.get('profiles',{}).items():
                print(name+': '+entry['state'])
                for w in entry['windows']:print('  '+str(w['window_minutes'])+'분 / 잔여 '+str(w['remaining_percent'])+'% / reset '+str(w['resets_at'])+' / '+w['source'])
            for w in result.get('windows',[]):print(w['group']+': '+str(w['window_minutes'])+'분 / 잔여 '+str(w['remaining_percent'])+'% / reset '+str(w['resets_at']))
        elif args.command=='setup' and not args.json:
            print('초기 환경 확인: '+result['agent'])
            for key,value in result['checks'].items():print('  '+key+': '+str(value))
            print('프로필: '+json.dumps(result['profiles'],ensure_ascii=False))
            print(result['authentication'])
            print('다음 단계:')
            for step in result['next_steps']:print('  - '+step)
            print('Orca의 새 대화에 붙여 넣을 요청:\n'+result['prompt'])
        else:
            print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
