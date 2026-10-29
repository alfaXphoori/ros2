"""Both nodes must exit cleanly on SIGINT (Ctrl+C) and SIGTERM (docker stop, launch)
without the 'rcl_shutdown already called' traceback."""
import os
import signal
import subprocess
import sys
import time

import pytest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')


@pytest.mark.parametrize('script,ready', [
    ('static_sensor_broadcaster.py', 'Published static transforms'),
    ('tf_obstacle_listener.py', 'Listening for transforms'),
])
@pytest.mark.parametrize('sig', [signal.SIGTERM, signal.SIGINT], ids=['SIGTERM', 'SIGINT'])
def test_clean_exit_on_signal(script, ready, sig):
    proc = subprocess.Popen([sys.executable, os.path.join(SRC, script)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(4.0)
    assert proc.poll() is None, 'node exited early'
    proc.send_signal(sig)
    try:
        out, err = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail('node did not stop within 15 s')
    log = out + err
    assert ready in log, log
    assert 'rcl_shutdown already called' not in log, log
    assert 'Traceback' not in log, log
    assert proc.returncode == 0, log
