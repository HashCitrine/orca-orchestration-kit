#!/usr/bin/env python3
"""Portable, conservative installer for Orca team skills (Python 3.9+)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

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
    fingerprint = digest(json.dumps({'config':config,'tools':observations},sort_keys=True).encode())
    previous = read_json(state/'capabilities.json', {})
    report = {'platform': platform.system(), 'tools': observations,
              'changed': previous.get('fingerprint') != fingerprint,
              'fingerprint': fingerprint, 'models': config.get('models', {}),
              'model_verification': 'runtime preflight required; defaults inherited',
              'skill_roots': {k:str(v) for k,v in roots(home,config).items()}}
    write_json(state/'capabilities.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install','update','uninstall','doctor'])
    parser.add_argument('--home',type=Path,default=Path.home(),help='isolated installation home for tests')
    args=parser.parse_args()
    state=args.home/'.config/orca-orchestration-kit'
    try:
        config=read_json(state/'config.json',{})
        if not isinstance(config,dict) or set(config)-{'executables','skill_roots','models','efforts','max_workers'}:
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
        if args.command=='doctor':
            result=doctor(args.home,config,state)
        else:
            source=Path(__file__).resolve().parent/'skills'/NAME
            if args.command!='uninstall' and not (source/'SKILL.md').is_file():
                raise ValueError('install/update must run from repository root kit.py')
            result=install(source,roots(args.home,config),state,args.command=='uninstall')
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
