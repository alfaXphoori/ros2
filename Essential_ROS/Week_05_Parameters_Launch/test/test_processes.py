"""Process-level shutdown tests.

* SIGTERM (docker stop, systemd, launch escalation) -> exit 0, no 'rcl_shutdown already called'
* Ctrl+C under `ros2 launch` delivers SIGINT twice (terminal process group + launch forwarding);
  the second one must not interrupt cleanup -> exit 0, no traceback
"""
import os
import signal
import subprocess
import time

import pytest
from ament_index_python.packages import get_package_prefix

PKG = 'amr_week05'
EXECUTABLES = ['fleet_parameters']


def start(exe):
    path = os.path.join(get_package_prefix(PKG), 'lib', PKG, exe)
    proc = subprocess.Popen([path, '--ros-args', '-r', '__ns:=/shutdown_test'],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(3.0)
    assert proc.poll() is None, proc.communicate()[0]
    return proc


def assert_clean(proc):
    out, _ = proc.communicate(timeout=20)
    assert 'rcl_shutdown already called' not in out
    assert 'Traceback' not in out, out
    assert proc.returncode == 0, out


@pytest.mark.parametrize('exe', EXECUTABLES)
def test_sigterm_clean_exit(exe):
    proc = start(exe)
    proc.send_signal(signal.SIGTERM)
    assert_clean(proc)


@pytest.mark.parametrize('gap', [0.005, 0.02, 0.05])
@pytest.mark.parametrize('exe', EXECUTABLES)
def test_double_sigint_clean_exit(exe, gap):
    proc = start(exe)
    proc.send_signal(signal.SIGINT)
    time.sleep(gap)
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
    assert_clean(proc)
