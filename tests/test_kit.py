import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('kit',Path(__file__).resolve().parents[1]/'kit.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)

class Tests(unittest.TestCase):
    def test_max_workers_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            state=home/'.config/orca-orchestration-kit'
            state.mkdir(parents=True)
            # Candidate discovery validates config without starting workers or probing tools.
            command=[sys.executable,str(Path(kit.__file__)), 'route', '--home',str(home),
                     '--task-type','implementation','--candidates']
            cases=[({},True),({'max_workers':None},True)]
            cases += [({'max_workers':value},True) for value in (1,2,3,8)]
            cases += [({'max_workers':value},False)
                      for value in (0,-1,True,False,'3',2.5,[],{})]
            for config,valid in cases:
                with self.subTest(config=config):
                    (state/'config.json').write_text(json.dumps(config),encoding='utf-8')
                    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
                    self.assertEqual(result.returncode,0 if valid else 1,result.stderr)
                    if valid:
                        self.assertIn('candidates',json.loads(result.stdout))
                    else:
                        self.assertIn('max_workers must be null (automatic) or a positive integer',result.stderr)

    def test_os_selection(self):
        for system,want in [('Darwin','orca'),('Windows','orca'),('Linux','orca-ide')]:
            self.assertEqual(kit.orca_command(system,{}),want)
        self.assertEqual(kit.orca_command('Linux',{'ORCA_CLI_COMMAND':'/a b/orca'}),'/a b/orca')
        self.assertEqual(kit.orca_command('Darwin',{'ORCA_DEV_REPO_ROOT':'/dev'}),'orca-dev')

    def test_lifecycle_and_conflicts(self):
        with tempfile.TemporaryDirectory(prefix='orca 한글 ') as directory:
            root=Path(directory).resolve();source=root/'source';source.mkdir()
            (source/'SKILL.md').write_text('v1')
            destinations={'a':root/'agent skills'};state=root/'state'
            kit.install(source,destinations,state)
            kit.install(source,destinations,state)
            target=destinations['a']/kit.NAME/'SKILL.md'
            target.write_text('user edit')
            with self.assertRaises(ValueError):kit.install(source,destinations,state)
            with self.assertRaises(ValueError):kit.install(source,destinations,state,True)
            self.assertEqual(target.read_text(),'user edit')
            target.write_text('v1');(source/'SKILL.md').write_text('v2')
            kit.install(source,destinations,state)
            self.assertEqual(target.read_text(),'v2')
            extra=target.parent/'user.txt';extra.write_text('keep')
            kit.install(source,destinations,state,True)
            self.assertFalse(target.exists());self.assertTrue(extra.exists())

    def test_unowned_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();source=root/'source';source.mkdir();(source/'SKILL.md').write_text('same')
            dest=root/'dest';(dest/kit.NAME).mkdir(parents=True);(dest/kit.NAME/'SKILL.md').write_text('same')
            with self.assertRaises(ValueError):kit.install(source,{'x':dest},root/'state')

    def test_context_reference_packaging_lifecycle(self):
        source = Path(kit.__file__).resolve().parent/'skills'/kit.NAME
        references = [Path('references/context-management.md'), Path('references/entire.md')]
        originals = {relative: (source/relative).read_bytes() for relative in references}
        with tempfile.TemporaryDirectory(prefix='orca context 한글 ') as directory:
            root = Path(directory).resolve()
            destinations = {agent: root/agent/'skills' for agent in ('codex','claude','agy','grok')}
            state = root/'state'
            kit.install(source, destinations, state)
            targets = {path/kit.NAME/relative: original
                       for path in destinations.values() for relative, original in originals.items()}
            for target, original in targets.items():
                self.assertEqual(target.read_bytes(), original)
            kit.install(source, destinations, state)
            for relative in references:
                edited = destinations['codex']/kit.NAME/relative
                original = originals[relative]
                with self.subTest(reference=str(relative)):
                    edited.write_bytes(original+b'\nuser edit\n')
                    with self.assertRaises(ValueError):
                        kit.install(source, destinations, state)
                    with self.assertRaises(ValueError):
                        kit.install(source, destinations, state, True)
                    self.assertEqual(edited.read_bytes(), original+b'\nuser edit\n')
                    for target, expected in targets.items():
                        if target != edited:
                            self.assertEqual(target.read_bytes(), expected)
                    edited.write_bytes(original)
            runtime = root/'workspace/.local/orca-team/runs/run-test/checkpoint.md'
            runtime.parent.mkdir(parents=True)
            runtime.write_text('local runtime state', encoding='utf-8')
            kit.install(source, destinations, state, True)
            for target in targets:
                self.assertFalse(target.exists())
            self.assertEqual(runtime.read_text(encoding='utf-8'), 'local runtime state')

    def test_cache_refresh_and_default_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            with patch.object(kit,'probe',return_value={'available':True,'interface_hash':'v1'}):
                a=kit.doctor(root,{},root/'state');b=kit.doctor(root,{},root/'state')
            self.assertTrue(a['changed']);self.assertFalse(b['changed']);self.assertEqual(a['models'],{})
            with patch.object(kit,'probe',return_value={'available':True,'interface_hash':'v2'}):
                self.assertTrue(kit.doctor(root,{},root/'state')['changed'])
            with patch.object(kit,'probe',return_value={'available':False}):
                c=kit.doctor(root,{'models':{'agy':'explicit'}},root/'state')
                self.assertTrue(c['changed']);self.assertFalse(c['tools']['agy']['available'])

    def orca(self,root,args):
        data=root/'Library/Application Support/orca/profiles/local-default/orca-data.json'
        data.parent.mkdir(parents=True,exist_ok=True)
        data.write_text(json.dumps({'settings':{'agentDefaultArgs':{'claude':args}}}))

    def test_claude_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();settings=root/'.claude/settings.json'
            self.assertEqual(kit.claude_readiness(root,'Darwin',{})['status'],'unknown')
            self.orca(root,'--dangerously-skip-permissions')
            self.assertEqual(kit.claude_readiness(root,'Darwin',{})['status'],'needs_claude_setup')
            settings.parent.mkdir();settings.write_text('{"skipDangerousModePermissionPrompt": true}')
            self.assertEqual(kit.claude_readiness(root,'Darwin',{})['status'],'ready')
            settings.unlink();self.orca(root,'--permission-mode acceptEdits')
            self.assertEqual(kit.claude_readiness(root,'Darwin',{})['status'],'ready')
            linux=root/'.config/orca/profiles/p/orca-data.json';linux.parent.mkdir(parents=True)
            linux.write_text(json.dumps({'settings':{'agentDefaultArgs':{'claude':'--permission-mode bypassPermissions'}}}))
            self.assertEqual(kit.claude_readiness(root,'Linux',{})['status'],'needs_claude_setup')

    def test_claude_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();settings=root/'.claude/settings.json'
            self.assertTrue(kit.claude_setup(root,{})['changed'])
            self.assertEqual(json.loads(settings.read_text()),{'skipDangerousModePermissionPrompt':True})
            original='{"model": "opus", "permissions": {"allow": ["Bash(ls)"]}}'
            settings.write_text(original);result=kit.claude_setup(root,{})
            self.assertEqual(Path(result['backup']).read_text(),original)
            merged=json.loads(settings.read_text())
            self.assertEqual(merged['model'],'opus');self.assertTrue(merged['skipDangerousModePermissionPrompt'])
            self.assertFalse(kit.claude_setup(root,{})['changed'])
            settings.write_text('{broken')
            with self.assertRaises(ValueError):kit.claude_setup(root,{})
            self.assertEqual(settings.read_text(),'{broken')
            custom=root/'custom claude'
            kit.claude_setup(root,{'CLAUDE_CONFIG_DIR':str(custom)})
            self.assertTrue(json.loads((custom/'settings.json').read_text())['skipDangerousModePermissionPrompt'])

    def test_doctor_reports_claude_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            with patch.object(kit,'probe',return_value={'available':True}), \
                 patch.object(kit,'claude_readiness',return_value={'status':'needs_claude_setup'}):
                a=kit.doctor(root,{},root/'state')
            with patch.object(kit,'probe',return_value={'available':True}), \
                 patch.object(kit,'claude_readiness',return_value={'status':'ready'}):
                b=kit.doctor(root,{},root/'state')
            self.assertEqual(a['claude_worker']['status'],'needs_claude_setup')
            self.assertTrue(b['changed']);self.assertEqual(b['claude_worker']['status'],'ready')

if __name__=='__main__':unittest.main()
