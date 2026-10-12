"""Supervisor refuses foreign cleanup and retains the real ownership boundary."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# Wrapper source preflight admits no Python cache directories in the worktree.
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    'gui_full_runner', Path(__file__).absolute().parents[1] / 'scripts/gui-full-runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class OwnershipTests(unittest.TestCase):
    def value(self, project='gate-test', directory='/owned/mirror', service='app'):
        return {'Config': {'Labels': {
            'com.docker.compose.project': project,
            'com.docker.compose.project.working_dir': directory,
            'com.docker.compose.service': service}}}

    def test_owned_primary_and_database(self):
        for service in ['app', 'db', 'runner', 'runner-full']:
            runner.owned(self.value(service=service), 'gate-test', Path('/owned/mirror'))

    def test_foreign_project_directory_or_service_refused(self):
        for value in [self.value(project='foreign'), self.value(directory='/foreign'),
                      self.value(service='foreign'), {'Config': {'Labels': None}}]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                runner.owned(value, 'gate-test', Path('/owned/mirror'))

    def test_cleanup_never_removes_foreign_container(self):
        cid = 'a' * 64
        with patch.object(runner, 'containers', return_value=[cid]), \
                patch.object(runner, 'inspect', return_value=self.value(project='foreign')), \
                patch.object(runner, 'output') as output:
            with self.assertRaises(RuntimeError):
                runner.cleanup('gate-test', Path('/owned/mirror'))
            output.assert_not_called()

    def test_cleanup_refuses_network_with_endpoints(self):
        nid = 'b' * 64
        network = {'Labels': {'com.docker.compose.project': 'gate-test'},
                   'Name': 'gate-test_default', 'Containers': {'foreign': {}}}
        with patch.object(runner, 'containers', return_value=[]), \
                patch.object(runner, 'output', side_effect=[nid, runner.json.dumps([network])]) as output:
            with self.assertRaises(RuntimeError):
                runner.cleanup('gate-test', Path('/owned/mirror'))
            self.assertEqual(len(output.call_args_list), 2)

    def test_cleanup_verifies_absence_after_exact_removal(self):
        cid, nid = 'a' * 64, 'b' * 64
        network = {'Labels': {'com.docker.compose.project': 'gate-test'},
                   'Name': 'gate-test_default', 'Containers': {}}
        with patch.object(runner, 'containers', side_effect=[[cid], []]), \
                patch.object(runner, 'inspect', return_value=self.value()), \
                patch.object(runner, 'output', side_effect=['', nid, runner.json.dumps([network]), '', '']):
            result = runner.cleanup('gate-test', Path('/owned/mirror'))
        self.assertEqual(result, {'verified': True, 'removed_containers': [cid], 'removed_networks': [nid]})


if __name__ == '__main__':
    unittest.main()
