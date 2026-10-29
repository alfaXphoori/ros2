"""Tests for domain_check.sh (RTPS port math) and `ros2 doctor --report`."""
import os
import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'src' / 'domain_check.sh'


def run_script(*args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    out = subprocess.run(['bash', str(SCRIPT), *args], env=env, capture_output=True,
                         text=True, timeout=60)
    return out


def port(output, label):
    m = re.search(re.escape(label) + r'[^:]*:\s*(\d+)', output)
    assert m, f'{label!r} not found in:\n{output}'
    return int(m.group(1))


def test_script_is_executable():
    assert os.access(SCRIPT, os.X_OK), 'domain_check.sh must be chmod +x'


@pytest.mark.parametrize('domain, spdp_mc, user_mc, spdp_uc, user_uc', [
    (0, 7400, 7401, 7410, 7411),
    (1, 7650, 7651, 7660, 7661),
    (7, 9150, 9151, 9160, 9161),
    (101, 32650, 32651, 32660, 32661),
])
def test_rtps_ports_from_env(domain, spdp_mc, user_mc, spdp_uc, user_uc):
    out = run_script(env_extra={'ROS_DOMAIN_ID': str(domain)})
    assert out.returncode == 0, out.stderr
    assert port(out.stdout, 'Discovery multicast') == spdp_mc
    assert port(out.stdout, 'User data multicast') == user_mc
    assert port(out.stdout, 'Discovery unicast') == spdp_uc
    assert port(out.stdout, 'User data unicast') == user_uc


def test_participant_id_adds_two_ports_per_participant():
    out = run_script('7', '3')
    assert out.returncode == 0, out.stderr
    # unicast ports move by PG=2 per participant, multicast ports do not
    assert port(out.stdout, 'Discovery multicast') == 9150
    assert port(out.stdout, 'Discovery unicast') == 7400 + 250 * 7 + 10 + 2 * 3
    assert port(out.stdout, 'User data unicast') == 7400 + 250 * 7 + 11 + 2 * 3


def test_high_domain_warns_about_ephemeral_ports():
    rng = Path('/proc/sys/net/ipv4/ip_local_port_range')
    if not rng.exists():
        pytest.skip('no /proc ephemeral range on this platform')
    lo, hi = map(int, rng.read_text().split())
    out = run_script('200')
    assert out.returncode == 0
    if 7400 + 250 * 200 <= hi and 7400 + 250 * 200 + 11 + 238 >= lo:
        assert 'overlaps the Linux ephemeral range' in out.stdout
    assert 'OK: no overlap' in run_script('7').stdout


def test_rejects_non_numeric_domain():
    out = run_script('abc')
    assert out.returncode == 2
    assert 'must be non-negative integers' in out.stderr


def test_ros2_doctor_report_lists_rmw():
    expected = os.environ.get('RMW_IMPLEMENTATION', 'rmw_fastrtps_cpp')
    out = subprocess.run(['ros2', 'doctor', '--report'], capture_output=True, text=True,
                         timeout=120)
    assert out.returncode == 0, out.stderr
    m = re.search(r'middleware name\s*:\s*(\S+)', out.stdout)
    assert m, out.stdout
    assert m.group(1) == expected
