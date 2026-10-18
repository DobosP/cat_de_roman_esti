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


class ArgumentTests(unittest.TestCase):
    sha = '1' * 40

    def base(self):
        return ['bash', str(runner.SOURCE / 'scripts/gate.sh'), 'full', '--sha', self.sha]

    def test_omitted_parallel_keeps_existing_wrapper_default(self):
        args = runner.parse_args(['--sha', self.sha])
        self.assertIsNone(args.parallel)
        self.assertFalse(args.fresh)
        self.assertEqual(runner.full_command(args.sha, fresh=args.fresh, parallel=args.parallel), self.base())

    def test_each_literal_parallel_is_forwarded_without_change(self):
        for value in ('1', '2', '3', '4'):
            with self.subTest(value=value):
                args = runner.parse_args(['--sha', self.sha, '--parallel', value])
                self.assertEqual(args.parallel, value)
                self.assertEqual(runner.full_command(args.sha, parallel=args.parallel),
                                 self.base() + ['--parallel', value])

    def test_fresh_and_parallel_preserve_sha_and_existing_flag_identity(self):
        self.assertEqual(runner.full_command(self.sha, fresh=True), self.base() + ['--fresh'])
        for flags in [ ['--fresh', '--parallel', '2'], ['--parallel', '2', '--fresh'] ]:
            with self.subTest(flags=flags):
                args = runner.parse_args(['--sha', self.sha, *flags])
                self.assertEqual(runner.full_command(args.sha, fresh=args.fresh, parallel=args.parallel),
                                 self.base() + ['--fresh', '--parallel', '2'])

    def test_invalid_parallel_cli_cannot_reach_runtime_or_cleanup(self):
        for flags in [ ['--parallel', value] for value in ('0', '5', '-1', '2.0', '02', '+2', ' 2', 'true') ] + [['--parallel']]:
            with self.subTest(flags=flags), \
                    patch.object(sys, 'argv', ['gui-full-runner.py', '--sha', self.sha, *flags]), \
                    patch.object(sys, 'stderr'), \
                    patch.object(runner, 'containers') as containers, \
                    patch.object(runner, 'output') as output, \
                    patch.object(runner.subprocess, 'Popen') as launch, \
                    patch.object(runner, 'cleanup') as cleanup:
                with self.assertRaises(SystemExit) as stopped:
                    runner.main()
                self.assertEqual(stopped.exception.code, 2)
                containers.assert_not_called()
                output.assert_not_called()
                launch.assert_not_called()
                cleanup.assert_not_called()

    def test_command_helper_refuses_invalid_parallel_and_sha(self):
        for value in (0, 2, 5, '0', '5', '02', '+2', '2.0'):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                runner.full_command(self.sha, parallel=value)
        for value in ('', '1' * 39, 'g' * 40, 'A' * 40):
            with self.subTest(sha=value), self.assertRaises(RuntimeError):
                runner.full_command(value, parallel='2')


if __name__ == '__main__':
    unittest.main()
