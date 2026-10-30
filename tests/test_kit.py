import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('kit',Path(__file__).resolve().parents[1]/'kit.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)

class Tests(unittest.TestCase):
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
