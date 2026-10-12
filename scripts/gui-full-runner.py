#!/usr/bin/env python3
"""Run the canonical full with its same-image legacy coordinator and owned cleanup.

  python3 -I scripts/gui-full-runner.py --sha <literal HEAD> [--fresh]

The wrapper remains the result authority. This supervisor supplies no gate input,
mount or result, and never changes trust. It discovers the real wrapper UUID and
primary container, then invokes the committed lifecycle before the managed intent.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

SOURCE = Path(__file__).absolute().parent.parent


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def regular_bytes(path):
    require(path.resolve() == path, 'Aliased input refused')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 2 * 1024 * 1024,
                'Nonregular or oversized input refused')
        raw = stream.read()
        after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), 'Input changed during read')
    return raw


def output(args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=20, cwd=SOURCE).stdout.strip()


def containers(project):
    return output(['docker', 'container', 'ls', '--all', '--no-trunc', '--filter',
                   'label=com.docker.compose.project=' + project, '--format', '{{.ID}}']).splitlines()


def inspect(cid):
    require(re.fullmatch(r'[0-9a-f]{64}', cid), 'Literal container ID required')
    return json.loads(output(['docker', 'container', 'inspect', cid]))[0]


def owned(value, project, mirror):
    labels = value['Config'].get('Labels') or {}
    require(labels.get('com.docker.compose.project') == project
            and labels.get('com.docker.compose.project.working_dir') == str(mirror)
            and labels.get('com.docker.compose.service') in {'app', 'db', 'runner', 'runner-full'},
            'Container ownership differs; refusing cleanup')
    return labels


def cleanup(project, mirror):
    removed = []
    for cid in containers(project):
        value = inspect(cid)
        owned(value, project, mirror)
        output(['docker', 'container', 'rm', '--force', cid])
        removed.append(cid)
    require(not containers(project), 'Owned containers remain')
    networks = output(['docker', 'network', 'ls', '--no-trunc', '--filter',
                       'label=com.docker.compose.project=' + project, '--format', '{{.ID}}']).splitlines()
    for nid in networks:
        require(re.fullmatch(r'[0-9a-f]{64}', nid), 'Literal network ID required')
        value = json.loads(output(['docker', 'network', 'inspect', nid]))[0]
        require(value['Labels'].get('com.docker.compose.project') == project
                and value['Name'] == project + '_default' and not value['Containers'],
                'Network ownership or empty-endpoint check failed')
        output(['docker', 'network', 'rm', nid])
    require(not output(['docker', 'network', 'ls', '--filter',
                        'label=com.docker.compose.project=' + project, '--format', '{{.ID}}']),
            'Owned network remains')
    return {'verified': True, 'removed_containers': removed, 'removed_networks': networks}


def stop(child, grace=25):
    if child and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--fresh', action='store_true')
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9a-f]{40}', args.sha), 'Full literal SHA required')
    require(SOURCE.resolve() == SOURCE and SOURCE.parents[1].name == '_worktrees',
            'Canonical task worktree required')
    require(os.getcwd() == str(SOURCE), 'Invoke from the Cat task worktree')
    require(not os.environ.get('GATE_OPERATOR'), 'Worker invocation required')
    require(output(['git', 'rev-parse', 'HEAD']) == args.sha
            and not output(['git', 'status', '--porcelain']), 'Clean literal HEAD required')
    require(output(['git', 'branch', '--show-current']) != 'main', 'Feature branch required')
    mirror = SOURCE.parents[2] / '_temp' / SOURCE.name / 'gates' / SOURCE.parent.name
    mirror.parent.mkdir(parents=True, exist_ok=True)
    key = SOURCE.parent.name + '-' + SOURCE.name + '-' + hashlib.sha256(str(SOURCE).encode()).hexdigest()[:12]
    project = 'gate-' + key
    # A second supervisor must not join or clean a first supervisor's run.
    with open(mirror.parent / (SOURCE.parent.name + '.full-supervisor.lock'), 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not containers(project), 'Existing gate containers require independent owner inspection')
        descriptor_path = mirror / '.gate/wrapper-current.json'
        previous = regular_bytes(descriptor_path) if descriptor_path.exists() else None
        gate = owner = None
        descriptor_raw = None
        acquired = False
        record = {'schema': 1, 'sha': args.sha, 'gate_exit': None, 'owner_exit': None,
                  'wrapper_invocation': None, 'errors': []}
        def interrupted(_signum, _frame):
            raise KeyboardInterrupt('Full supervisor interrupted')
        signal.signal(signal.SIGTERM, interrupted)
        try:
            command = ['bash', str(SOURCE / 'scripts/gate.sh'), 'full', '--sha', args.sha]
            if args.fresh:
                command.append('--fresh')
            gate = subprocess.Popen(command, cwd=SOURCE, start_new_session=True)
            deadline = time.monotonic() + 7200
            while gate.poll() is None:
                require(time.monotonic() < deadline, 'Full supervisor deadline exceeded')
                if not acquired:
                    # The wrapper's own FD9 flock proves this child acquired the
                    # lane. A competing direct gate cannot grant cleanup authority.
                    try:
                        fd = Path(f'/proc/{gate.pid}/fd/9')
                        expected = (mirror.parent / (SOURCE.parent.name + '.lock')).stat()
                        actual = fd.stat()
                        info = Path(f'/proc/{gate.pid}/fdinfo/9').read_text()
                        acquired = (expected.st_dev, expected.st_ino) == (actual.st_dev, actual.st_ino) \
                            and bool(re.search(r'lock:\s+\d+: FLOCK\s+ADVISORY\s+WRITE\s+\d+\s', info))
                    except FileNotFoundError:
                        pass
                if acquired and owner is None and descriptor_path.exists():
                    try:
                        raw = regular_bytes(descriptor_path)
                        target_raw = regular_bytes(mirror / '.gate/full/wrapper-current.json')
                    except FileNotFoundError:
                        time.sleep(0.2)
                        continue
                    if raw != target_raw:
                        time.sleep(0.2)
                        continue
                    if raw != previous:
                        descriptor = json.loads(raw)
                        require(descriptor['target'] == 'full' and descriptor['sha'] == args.sha
                                and re.fullmatch(r'[0-9a-f-]{36}', descriptor['invocation'])
                                and re.fullmatch(r'[0-9a-f]{64}', descriptor['tree_sha256']),
                                'Actual full descriptor differs')
                        require(descriptor_raw is None or descriptor_raw == raw, 'Full invocation changed')
                        descriptor_raw = raw
                        record['wrapper_invocation'] = descriptor['invocation']
                        for cid in containers(project):
                            value = inspect(cid)
                            labels = owned(value, project, mirror)
                            if labels['com.docker.compose.service'] != 'app':
                                continue
                            require(labels.get('org.opencontainers.image.revision') == args.sha
                                    and labels.get('org.roedu.tree-sha256') == descriptor['tree_sha256'],
                                    'Primary source/tree differs')
                            if not value['State']['Running']:
                                continue
                            directory = mirror / '.gate/full/legacy-owner' / descriptor['invocation']
                            owner = subprocess.Popen(['python3', '-I', str(SOURCE / 'scripts/gui-owner-lifecycle.py'),
                                                      str(directory), cid], cwd=SOURCE, start_new_session=True)
                            print('Attached legacy coordinator to actual full ' + descriptor['invocation'], flush=True)
                            break
                time.sleep(1)
            record['gate_exit'] = gate.wait()
            if owner is not None:
                record['owner_exit'] = owner.wait(timeout=30)
            require(owner is not None and record['owner_exit'] == 0, 'Same-full owner lifecycle did not pass')
        except BaseException as error:
            record['errors'].append(type(error).__name__ + ': ' + str(error))
        finally:
            # Owner cleanup must run while the primary is still available.
            stop(owner, grace=180)
            stop(gate)
            if gate is not None:
                record['gate_exit'] = gate.returncode
            if owner is not None:
                record['owner_exit'] = owner.returncode
            try:
                if acquired and descriptor_raw is not None:
                    require(regular_bytes(descriptor_path) == descriptor_raw,
                            'Another full invocation appeared; cleanup refused')
                    legacy_ids = output(['docker', 'container', 'ls', '--all', '--no-trunc', '--filter',
                                         'label=org.roedu.owner-legacy-run=' + record['wrapper_invocation'],
                                         '--format', '{{.ID}}'])
                    require(not legacy_ids, 'UUID-owned legacy container remains; inspect before another runtime')
                    # Reacquire the wrapper lane after its exit. Holding this lock
                    # prevents another direct wrapper from creating new resources.
                    with open(mirror.parent / (SOURCE.parent.name + '.lock'), 'a') as gate_lock:
                        fcntl.flock(gate_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        require(regular_bytes(descriptor_path) == descriptor_raw, 'Full invocation changed before cleanup')
                        record['cleanup'] = cleanup(project, mirror)
                else:
                    require(not containers(project), 'No acquired invocation; cleanup authority absent')
                    record['cleanup'] = {'verified': True, 'removed_containers': [], 'removed_networks': []}
            except Exception as error:
                record['errors'].append('cleanup: ' + str(error))
            destination = SOURCE / '.gate/full/supervisor.json'
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, 'w') as stream:
                json.dump(record, stream, indent=2, sort_keys=True)
                stream.write('\n')
            print(json.dumps(record, separators=(',', ':')), flush=True)
        return 2 if record['errors'] else record['gate_exit']


if __name__ == '__main__':
    sys.exit(main())
