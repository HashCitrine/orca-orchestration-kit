import importlib.util
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

if __name__=='__main__':unittest.main()
