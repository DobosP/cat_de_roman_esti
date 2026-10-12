#!/usr/bin/env python3
"""Same-full legacy container custody; invoked by gui-full-runner.py, never a gate result."""
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

if not __debug__:
    raise RuntimeError('Owner custody assertions are mandatory; invoke python3 -I')

SOURCE = Path(__file__).absolute().parent.parent
MIRROR = SOURCE.parents[2] / '_temp' / SOURCE.name / 'gates' / SOURCE.parent.name
FIELDS = {'schema', 'target', 'run_id', 'runner_invocation', 'source_sha', 'tree_sha256', 'toolchain_digest',
          'wrapper_invocation', 'descriptor_sha256', 'primary_cid', 'app_image_id',
          'current_manifest_sha256', 'current_versions_lock_sha256', 'expected_legacy_policy_stage'}
FORMAT = ('{"id":{{json .Id}},"image":{{json .Image}},"name":{{json .Name}},'
          '"running":{{json .State.Running}},"pid":{{json .State.Pid}},'
          '"sha":{{json (index .Config.Labels "org.opencontainers.image.revision")}},'
          '"tree":{{json (index .Config.Labels "org.roedu.tree-sha256")}},'
          '"owner_run":{{json (index .Config.Labels "org.roedu.owner-legacy-run")}},'
          '"owner_primary":{{json (index .Config.Labels "org.roedu.owner-primary")}},'
          '"user":{{json .Config.User}},"entrypoint":{{json .Config.Entrypoint}},'
          '"cmd":{{json .Config.Cmd}},"network":{{json .HostConfig.NetworkMode}},'
          '"ports":{{json .HostConfig.PortBindings}},"mounts":{{json .Mounts}},'
          '"readonly":{{json .HostConfig.ReadonlyRootfs}},"memory":{{json .HostConfig.Memory}},'
          '"cpus":{{json .HostConfig.NanoCpus}},"pids":{{json .HostConfig.PidsLimit}},'
          '"cap_drop":{{json .HostConfig.CapDrop}},"security":{{json .HostConfig.SecurityOpt}}}')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_size <= 2 * 1024 * 1024
        data = stream.read()
        after = os.fstat(stream.fileno())
        assert (info.st_ino, info.st_size, info.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
        return data

def save(name, data):
    assert re.fullmatch(r'[a-z0-9.-]+', name)
    pending = root / (name + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(pending, root / name, follow_symlinks=False)  # Atomic, refuses existing destination.
    os.unlink(pending)  # Only the fresh file just created by this call.

def record(name, value):
    save(name, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())

def run(args):
    number = len(commands)
    item = {'args': args, 'exit_code': None, 'timeout': False}
    commands.append(item)
    out = err = b''
    child = None
    try:
        child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            out, err = child.communicate(timeout=15)
        except subprocess.TimeoutExpired as error:
            out, err = error.output or b'', error.stderr or b''
            item['timeout'] = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                out, err = child.communicate(timeout=2)
            except subprocess.TimeoutExpired as error:
                out, err = error.output or out, error.stderr or err
                os.killpg(child.pid, signal.SIGKILL)
                out, err = child.communicate(timeout=2)
        item['exit_code'] = child.returncode
    except Exception as error:
        item['error'] = type(error).__name__
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
                out, err = child.communicate(timeout=2)
            except Exception:
                item['reap_incomplete'] = True
    finally:
        save(f'{number:02}.stdout', out)
        save(f'{number:02}.stderr', err)
        item['stdout_sha256'], item['stderr_sha256'] = digest(out), digest(err)
    assert item['exit_code'] == 0 and not item['timeout'] and 'error' not in item, 'Docker operation failed'
    return out

def inspect(cid):
    assert re.fullmatch(r'[0-9a-f]{64}', cid)
    return json.loads(run(['docker', 'container', 'inspect', '--format', FORMAT, cid]))

def ids(*filters):
    args = ['docker', 'container', 'ls', '--all', '--no-trunc']
    for value in filters:
        args += ['--filter', value]
    result = run(args + ['--format', '{{.ID}}']).decode().splitlines()
    assert all(re.fullmatch(r'[0-9a-f]{64}', cid) for cid in result)
    return result

def primary_ok(value):
    assert value['id'] == request['primary_cid'] and value['image'] == request['app_image_id']
    assert value['running'] and value['sha'] == request['source_sha'] and value['tree'] == request['tree_sha256']
    assert value['user'] == '10001:10001' and value['entrypoint'] == ['/app'] and not value['ports']

assert len(sys.argv) == 3
root = Path(sys.argv[1])
primary_cid = sys.argv[2]
assert re.fullmatch(r'[0-9a-f]{64}', primary_cid)
assert root.parent == MIRROR / '.gate/full/legacy-owner'
waiting_until = time.monotonic() + 3600
while not (root / 'intent.json').exists():
    assert time.monotonic() < waiting_until, 'Actual full did not request legacy within owner deadline'
    time.sleep(0.2)
for path in [MIRROR, MIRROR / '.gate', MIRROR / '.gate/full', root.parent, root]:
    info = path.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and path.resolve() == path
assert stat.S_IMODE(root.lstat().st_mode) == 0o700
intent_raw = read(root / 'intent.json')
request = json.loads(intent_raw)
assert set(request) == FIELDS - {'primary_cid'} and request['schema'] == 1 and request['target'] == 'full'
request['primary_cid'] = primary_cid
request_raw = (json.dumps(request, indent=2, sort_keys=True) + '\n').encode()
request_path = root / 'request.json'
assert re.fullmatch(r'[0-9a-f-]{36}', request['run_id']) and root.name == request['run_id']
assert request['run_id'] == request['wrapper_invocation']
assert re.fullmatch(r'[0-9a-f]{40}', request['source_sha'])
assert all(re.fullmatch(r'[0-9a-f]{64}', request[k]) for k in ['tree_sha256', 'descriptor_sha256', 'primary_cid', 'current_manifest_sha256', 'current_versions_lock_sha256'])
assert re.fullmatch(r'sha256:[0-9a-f]{64}', request['app_image_id'])
assert request['expected_legacy_policy_stage'] in ['report-only', 'enforced']
descriptor_raw = read(MIRROR / '.gate/full/wrapper-current.json')
descriptor = json.loads(descriptor_raw)
assert digest(descriptor_raw) == request['descriptor_sha256'] and descriptor['target'] == 'full'
for key in ['source_sha', 'tree_sha256', 'toolchain_digest', 'wrapper_invocation']:
    descriptor_key = {'source_sha': 'sha', 'wrapper_invocation': 'invocation'}.get(key, key)
    assert descriptor[descriptor_key] == request[key]
bootstrap = json.loads(read(MIRROR / '.gate/full/bootstrap-execution.json'))
assert bootstrap['invocation'] == request['runner_invocation'] and bootstrap['wrapper_invocation'] == request['wrapper_invocation']
assert bootstrap['sha'] == request['source_sha'] and bootstrap['tree_sha256'] == request['tree_sha256']
save('request.json', request_raw)
waiting_until = time.monotonic() + 60
while not (root / 'preflight.json').exists():
    assert time.monotonic() < waiting_until, 'Managed full preflight absent'
    time.sleep(0.2)
preflight_raw = read(root / 'preflight.json')
preflight = json.loads(preflight_raw)
assert preflight['status'] == 'pass' and preflight['request_sha256'] == digest(request_raw) and preflight['port_8081_closed']
stage_lines = [line for line in read(MIRROR / '.gate.env').decode().splitlines() if line.startswith('CSP_STAGE=')]
assert len(stage_lines) == 1 and stage_lines[0] in ['CSP_STAGE=report-only', 'CSP_STAGE=enforced']
stage = stage_lines[0].split('=', 1)[1]
assert preflight['actual_csp_stage'] == stage
assert request['expected_legacy_policy_stage'] == stage
commands, errors = [], []
method_raw = read(Path(__file__))
def interrupted(_signum, _frame):
    raise KeyboardInterrupt('Owned lifecycle interrupted')
signal.signal(signal.SIGTERM, interrupted)
cid = None
name = 'roedu-cat-legacy-' + request['run_id']
before = None
cleaned = False
try:
    before = inspect(request['primary_cid'])
    primary_ok(before)
    assert not ids('name=^/' + name + '$'), 'Owned name already exists'
    assert not (root / 'abort.json').exists(), 'Consumer aborted before legacy launch'
    args = ['docker', 'run', '--detach', '--pull=never', '--name', name, '--restart=no', '--init',
            '--label', 'org.roedu.owner-legacy-run=' + request['run_id'],
            '--label', 'org.roedu.owner-primary=' + request['primary_cid'],
            '--network', 'container:' + request['primary_cid'], '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--cpus', '2', '--memory', '2g', '--pids-limit', '128',
            '--no-healthcheck', '--env', 'CAT_UI=legacy', '--env', 'CAT_ACCOUNTS_ENABLED=0',
            '--env', 'CAT_CSP_ENFORCE=' + ('true' if stage == 'enforced' else 'false'),
            request['app_image_id'], '-listen', '127.0.0.1:8081']
    cid = run(args).decode().strip()
    value = inspect(cid)
    assert cid != request['primary_cid'] and value['name'] == '/' + name
    assert value['image'] == request['app_image_id'] and value['running']
    assert value['owner_run'] == request['run_id'] and value['owner_primary'] == request['primary_cid']
    assert value['network'] == 'container:' + request['primary_cid'] and not value['ports'] and not value['mounts']
    assert value['readonly'] and value['memory'] == 2 * 1024**3 and value['cpus'] == 2_000_000_000 and value['pids'] == 128
    assert value['cap_drop'] == ['ALL'] and 'no-new-privileges' in value['security']
    assert value['user'] == '10001:10001' and value['entrypoint'] == ['/app'] and value['cmd'] == ['-listen', '127.0.0.1:8081']
    record('owner-ready.json', {'request_sha256': digest(request_raw), 'preflight_sha256': digest(preflight_raw), 'primary': before, 'legacy': value, 'status': 'ready'})
    deadline = time.monotonic() + 300
    while not (root / 'probe-result.json').exists():
        if (root / 'abort.json').exists():
            abort = json.loads(read(root / 'abort.json'))
            assert abort['intent_sha256'] == digest(intent_raw)
            raise RuntimeError('Actual consumer command failed; remove only the owned legacy container')
        assert time.monotonic() < deadline, 'Managed witness deadline exceeded'
        time.sleep(0.2)
    probe = json.loads(read(root / 'probe-result.json'))
    assert probe['request_sha256'] == digest(request_raw) and probe['status'] == 'pass' and not probe['errors']
    assert probe['legacy_cid'] == cid and probe['journey']['real_board_visible'] is True
    for key in ['source_sha', 'tree_sha256', 'toolchain_digest', 'wrapper_invocation', 'runner_invocation', 'app_image_id']:
        assert probe[{'source_sha': 'source'}.get(key, key)] == request[key]
    assert type(probe['legacy_violations']) is int and probe['legacy_violations'] >= 0
    value_after = inspect(cid)
    assert value_after['image'] == value['image'] and value_after['pid'] == value['pid'] and value_after['running']
    record('legacy-after.json', value_after)
except BaseException as error:
    errors.append(type(error).__name__ + ': ' + str(error))
finally:
    try:
        found = ids('name=^/' + name + '$', 'label=org.roedu.owner-legacy-run=' + request['run_id'])
        assert len(found) <= 1
        if found:
            owned = inspect(found[0])
            assert owned['id'] != request['primary_cid'] and (cid is None or owned['id'] == cid)
            assert owned['name'] == '/' + name and owned['image'] == request['app_image_id']
            assert owned['owner_run'] == request['run_id'] and owned['owner_primary'] == request['primary_cid']
            try:
                run(['docker', 'container', 'logs', '--timestamps', '--tail', '200', owned['id']])
            except Exception as error:
                errors.append('bounded server log acquisition: ' + type(error).__name__)
            run(['docker', 'container', 'rm', '--force', owned['id']])
            assert not ids('id=' + owned['id'])
        assert not ids('name=^/' + name + '$')
        cleaned = True
    except BaseException as error:
        errors.append('cleanup: ' + type(error).__name__ + ': ' + str(error))
    try:
        after = inspect(request['primary_cid'])
        primary_ok(after)
        if before is not None:
            assert after == before, 'Primary container changed'
        record('primary-after.json', after)
        assert read(request_path) == request_raw and read(MIRROR / '.gate/full/wrapper-current.json') == descriptor_raw
        assert read(root / 'intent.json') == intent_raw and read(root / 'preflight.json') == preflight_raw
        assert read(Path(__file__)) == method_raw
    except BaseException as error:
        errors.append('after: ' + type(error).__name__ + ': ' + str(error))
    record('owner-lifecycle.json', {'status': 'pass' if not errors and cleaned else 'fail',
           'request_sha256': digest(request_raw), 'commands': commands, 'errors': errors, 'cleanup_verified': cleaned,
           'method_sha256': digest(method_raw),
           'scope': 'Owner custody for one actual same-full legacy witness; no aggregate-green/E3/qualification claim.'})
sys.exit(1 if errors or not cleaned else 0)
