"""Validate the Open-RMF fleet config + nav graph with the REAL rmf_fleet_adapter parser.

rmf_adapter.easy_full_control.FleetConfiguration.from_config_files() is the
function the EasyFullControl fleet adapter calls at start-up; it returns None
(and prints why) when a required section is missing.
"""
import os
import textwrap

import pytest
import yaml

from amr_adv04.fleet_config_check import (cross_check, graph_lanes, graph_waypoints,
                                          load_fleet_config, main)

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, '..', 'config', 'fleet_adapter_config.yaml')
NAV_GRAPH = os.path.join(HERE, '..', 'config', 'nav_graph.yaml')

# The configuration that shipped with this module before it was fixed
OLD_CONFIG = textwrap.dedent("""
    rmf_fleet:
      name: "warehouse_amr_fleet"
      limits:
        linear: [0.8, 0.5]
        angular: [1.2, 1.5]
      profile:
        footprint: 0.3
        vicinity: 0.5
      reversible: false
      battery_system:
        voltage: 24.0
        capacity: 40.0
        charging_current: 10.0
        recharge_threshold: 0.20
        drain_battery_factor: 1.0
      robots:
        amr_01:
          charger: "charger_alpha"
          initial_waypoint: "pickup_bay_1"
        amr_02:
          charger: "charger_beta"
          initial_waypoint: "dropoff_bay_2"
""")


@pytest.fixture(scope='module')
def cfg():
    return load_fleet_config(CONFIG, NAV_GRAPH)


@pytest.fixture(scope='module')
def raw():
    with open(CONFIG) as f:
        return yaml.safe_load(f)


def test_parser_accepts_config(cfg):
    assert cfg.fleet_name == 'warehouse_amr_fleet'


def test_robots_and_chargers(cfg):
    assert sorted(cfg.known_robots) == ['amr_01', 'amr_02']
    chargers = {r: c.compatible_chargers for r, c in cfg.known_robot_configurations.items()}
    assert chargers == {'amr_01': ['charger_alpha'], 'amr_02': ['charger_beta']}


def test_battery_policy(cfg):
    assert cfg.recharge_threshold == pytest.approx(0.20)
    assert cfg.recharge_soc == pytest.approx(1.0)
    assert cfg.account_for_battery_drain is True
    assert cfg.max_delay.total_seconds() == pytest.approx(10.0)
    assert cfg.update_interval.total_seconds() == pytest.approx(0.1)   # 10 Hz


def test_nav_graph(cfg):
    names = {w.waypoint_name: w for w in graph_waypoints(cfg.graph)}
    assert set(names) == {'charger_alpha', 'charger_beta', 'junction_a', 'junction_b',
                          'pickup_bay_1', 'dropoff_bay_2'}
    assert names['charger_alpha'].charger and names['charger_beta'].charger
    assert list(names['charger_beta'].location) == pytest.approx([0.0, 1.5])
    assert all(w.map_name == 'L1' for w in names.values())
    assert len(graph_lanes(cfg.graph)) == 12


def test_cross_checks_pass(cfg, raw):
    assert cross_check(cfg, raw) == []


def test_cli_exit_code_ok(capsys):
    assert main(['--config', CONFIG, '--nav-graph', NAV_GRAPH]) == 0
    assert 'OK:' in capsys.readouterr().out


def test_old_config_is_rejected_by_rmf(tmp_path):
    bad = tmp_path / 'old_fleet.yaml'
    bad.write_text(OLD_CONFIG)
    with pytest.raises(ValueError):
        load_fleet_config(str(bad), NAV_GRAPH)
    assert main(['--config', str(bad), '--nav-graph', NAV_GRAPH]) == 1


@pytest.mark.parametrize('section', ['mechanical_system', 'ambient_system', 'tool_system',
                                     'battery_system', 'profile', 'limits'])
def test_each_required_section(tmp_path, raw, section):
    data = yaml.safe_load(yaml.safe_dump(raw))
    del data['rmf_fleet'][section]
    p = tmp_path / f'no_{section}.yaml'
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        load_fleet_config(str(p), NAV_GRAPH)


def test_unknown_charger_is_caught(tmp_path, raw):
    data = yaml.safe_load(yaml.safe_dump(raw))
    data['rmf_fleet']['robots']['amr_02']['charger'] = 'charger_gamma'
    p = tmp_path / 'bad_charger.yaml'
    p.write_text(yaml.safe_dump(data))
    cfg = load_fleet_config(str(p), NAV_GRAPH)   # the parser itself accepts it ...
    errors = cross_check(cfg, data)               # ... so we must cross-check
    assert any('charger_gamma' in e for e in errors)


def test_nav_graph_without_levels_raises(tmp_path):
    g = tmp_path / 'graph.yaml'
    g.write_text('building_name: x\n')
    with pytest.raises(RuntimeError):
        load_fleet_config(CONFIG, str(g))
