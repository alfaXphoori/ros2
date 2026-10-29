"""SROS2 (DDS-Security) in Enforce mode, for real - no mocks.

1. create a keystore + two enclaves in a temp dir (`ros2 security ...`)
2. Enforce without `--enclave` (and no enclave "/") -> the process refuses to start
3. secured talker + secured listener (each with its own enclave) -> messages arrive
4. an unsecured listener on the same domain -> receives nothing
   (DDS-Security handshake: allow_unauthenticated_participants=false in the
   sros2 default governance, and topic data is encrypted)

Run:  colcon test --packages-select amr_adv05
      python3 -m pytest -v Advanced_ROS/05_Production_CI_CD_Security/test/test_sros2_enforce.py
"""
import os
import signal
import subprocess
import time

import pytest

TALKER_ENCLAVE = '/talker_listener/talker'
LISTENER_ENCLAVE = '/talker_listener/listener'
HEARD = 'I heard: [Hello World'


def _base_env():
    env = dict(os.environ)
    for k in list(env):
        if k.startswith('ROS_SECURITY_'):
            del env[k]
    env['PYTHONUNBUFFERED'] = '1'
    env['RCUTILS_LOGGING_BUFFERED_STREAM'] = '0'
    return env


def _secure_env(keystore):
    env = _base_env()
    env.update(ROS_SECURITY_KEYSTORE=str(keystore), ROS_SECURITY_ENABLE='true',
               ROS_SECURITY_STRATEGY='Enforce')
    return env


def _start(cmd, env, log_path):
    log = open(log_path, 'w')
    proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    proc.log_file = log
    proc.log_path = log_path
    return proc


def _stop(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    proc.log_file.close()
    with open(proc.log_path) as f:
        return f.read()


def _wait_for_text(path, text, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        with open(path) as f:
            if text in f.read():
                return True
        time.sleep(0.2)
    return False


@pytest.fixture(scope='module')
def keystore(tmp_path_factory):
    ks = tmp_path_factory.mktemp('sros2') / 'sros2_keystore'
    env = _base_env()
    subprocess.run(['ros2', 'security', 'create_keystore', str(ks)],
                   env=env, check=True, capture_output=True, timeout=60)
    for enclave in (TALKER_ENCLAVE, LISTENER_ENCLAVE):
        subprocess.run(['ros2', 'security', 'create_enclave', str(ks), enclave],
                       env=env, check=True, capture_output=True, timeout=60)
    return ks


def test_keystore_layout(keystore):
    for enclave in (TALKER_ENCLAVE, LISTENER_ENCLAVE):
        d = keystore / 'enclaves' / enclave.lstrip('/')
        for f in ('cert.pem', 'key.pem', 'permissions.p7s', 'governance.p7s',
                  'identity_ca.cert.pem', 'permissions_ca.cert.pem'):
            assert (d / f).is_file(), f'missing {d / f}'
    assert (keystore / 'public' / 'ca.cert.pem').is_file()
    assert (keystore / 'private' / 'ca.key.pem').is_file()


def test_enforce_without_enclave_refuses_to_start(keystore, tmp_path):
    # No --enclave -> rcl looks for enclave "/" which the keystore does not have.
    proc = subprocess.run(['ros2', 'run', 'demo_nodes_py', 'talker'],
                          env=_secure_env(keystore), capture_output=True, text=True,
                          timeout=60)
    out = proc.stdout + proc.stderr
    (tmp_path / 'enforce_no_enclave.txt').write_text(out)
    assert proc.returncode != 0, out
    assert 'enclave' in out.lower() or 'security' in out.lower(), out


def test_secured_pair_communicates_and_unsecured_listener_gets_nothing(keystore,
                                                                         tmp_path):
    secure = _secure_env(keystore)
    talker = _start(['ros2', 'run', 'demo_nodes_py', 'talker',
                     '--ros-args', '--enclave', TALKER_ENCLAVE],
                    secure, tmp_path / 'talker.txt')
    listener = _start(['ros2', 'run', 'demo_nodes_py', 'listener',
                       '--ros-args', '--enclave', LISTENER_ENCLAVE],
                      secure, tmp_path / 'listener.txt')
    intruder = _start(['ros2', 'run', 'demo_nodes_py', 'listener',
                       '--ros-args', '-r', '__node:=intruder'],
                      _base_env(), tmp_path / 'intruder.txt')
    try:
        heard = _wait_for_text(tmp_path / 'listener.txt', HEARD, timeout=30)
        # give the unsecured listener the same number of seconds of traffic
        time.sleep(5.0)
        still_running = talker.poll() is None and intruder.poll() is None
    finally:
        out_t, out_l, out_i = _stop(talker), _stop(listener), _stop(intruder)
    assert still_running, f'talker:\n{out_t}\nintruder:\n{out_i}'
    assert heard, f'secured listener heard nothing\ntalker:\n{out_t}\nlistener:\n{out_l}'
    assert 'Publishing' in out_t
    assert HEARD not in out_i, f'unsecured listener received data:\n{out_i}'
