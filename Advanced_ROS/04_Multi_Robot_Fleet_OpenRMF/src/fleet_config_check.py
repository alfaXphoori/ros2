#!/usr/bin/env python3
"""
Tutorial 04: validate an Open-RMF fleet configuration for real.

Loads fleet_adapter_config.yaml + nav_graph.yaml with the same C++ parser the
EasyFullControl fleet adapter uses at start-up
(rmf_adapter.easy_full_control.FleetConfiguration.from_config_files) and then
checks the cross-file references that the parser itself does not check
(robot chargers must be is_charger waypoints of the nav graph, ...).

  ros2 run amr_adv04 fleet_config_check
  ros2 run amr_adv04 fleet_config_check --config my_fleet.yaml --nav-graph my_graph.yaml

Exit code 0 = valid, 1 = invalid.
"""

import argparse
import os
import sys

import yaml


def default_paths():
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory('amr_adv04')
    return (os.path.join(share, 'config', 'fleet_adapter_config.yaml'),
            os.path.join(share, 'config', 'nav_graph.yaml'))


def load_fleet_config(config_path, nav_graph_path):
    """Parse both files with rmf_fleet_adapter. Returns the FleetConfiguration.

    Raises ValueError if from_config_files() rejects the fleet config (it
    returns None and prints the reason on stdout), RuntimeError if the nav
    graph cannot be parsed.
    """
    import rmf_adapter.easy_full_control as efc
    cfg = efc.FleetConfiguration.from_config_files(config_path, nav_graph_path)
    sys.stdout.flush()
    if cfg is None:
        raise ValueError(f'rmf_fleet_adapter rejected {config_path} '
                         '(see the message printed above)')
    return cfg


def graph_waypoints(graph):
    return [graph.get_waypoint(i) for i in range(graph.num_waypoints)]


def graph_lanes(graph):
    lanes = []
    for i in range(graph.num_lanes):
        lane = graph.get_lane(i)
        lanes.append((lane.entry.waypoint_index, lane.exit.waypoint_index))
    return lanes


def cross_check(cfg, raw):
    """Checks the parser does not do. Returns a list of error strings.

    Note: we deliberately do not touch cfg.vehicle_traits / cfg.battery_system
    from Python - with rmf_fleet_adapter_python 2.7.2 those getters corrupt the
    heap (crash at interpreter exit). Their values come straight from the YAML.
    """
    errors = []
    graph = cfg.graph
    chargers = {w.waypoint_name for w in graph_waypoints(graph) if w.charger}
    for robot, rc in cfg.known_robot_configurations.items():
        if not rc.compatible_chargers:
            errors.append(f'robot {robot} has no charger')
        for ch in rc.compatible_chargers:
            if ch not in chargers:
                errors.append(f'robot {robot}: charger "{ch}" is not an is_charger '
                              f'waypoint of the nav graph (chargers: {sorted(chargers)})')
    if not 0.0 <= cfg.recharge_threshold < cfg.recharge_soc <= 1.0:
        errors.append(f'need 0 <= recharge_threshold ({cfg.recharge_threshold}) < '
                      f'recharge_soc ({cfg.recharge_soc}) <= 1')
    profile = raw['rmf_fleet']['profile']
    if profile['vicinity'] < profile['footprint']:
        errors.append('profile.vicinity must be >= profile.footprint')
    lanes = set(graph_lanes(graph))
    for a, b in sorted(lanes):
        if (b, a) not in lanes:
            errors.append(f'lane {a}->{b} has no reverse lane (one-way on purpose?)')
    return errors


def summary_lines(cfg, raw):
    f = raw['rmf_fleet']
    g = cfg.graph
    lines = [
        f'fleet_name            : {cfg.fleet_name}',
        f'limits linear/angular : {f["limits"]["linear"]} / {f["limits"]["angular"]}',
        f'footprint / vicinity  : {f["profile"]["footprint"]} m / {f["profile"]["vicinity"]} m',
        f'recharge_threshold    : {cfg.recharge_threshold:.2f}',
        f'recharge_soc          : {cfg.recharge_soc:.2f}',
        f'account_for_battery_drain: {cfg.account_for_battery_drain}',
        f'responsive_wait       : {cfg.default_responsive_wait}',
        f'max_delay             : {cfg.max_delay.total_seconds():.1f} s',
        f'fleet state period    : {cfg.update_interval.total_seconds():.2f} s',
        f'nav graph             : {g.num_waypoints} waypoints, {g.num_lanes} lanes',
    ]
    for w in graph_waypoints(g):
        flags = [n for n, v in (('charger', w.charger), ('parking', w.parking_spot),
                                ('holding', w.holding_point)) if v]
        x, y = w.location
        lines.append(f'  [{w.index}] {w.waypoint_name:<14} {w.map_name} '
                     f'({x:4.1f}, {y:4.1f}) {",".join(flags)}')
    for robot in sorted(cfg.known_robots):
        rc = cfg.get_known_robot_configuration(robot)
        lines.append(f'robot {robot:<15} : chargers={rc.compatible_chargers}')
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[1])
    parser.add_argument('--config', help='fleet config YAML (default: installed amr_adv04)')
    parser.add_argument('--nav-graph', help='nav graph YAML (default: installed amr_adv04)')
    args, _ = parser.parse_known_args(argv)
    config, nav_graph = args.config, args.nav_graph
    if config is None or nav_graph is None:
        d_config, d_graph = default_paths()
        config = config or d_config
        nav_graph = nav_graph or d_graph

    print(f'config   : {config}\nnav graph: {nav_graph}', flush=True)
    try:
        cfg = load_fleet_config(config, nav_graph)
    except (ValueError, RuntimeError) as exc:
        print(f'INVALID: {exc}')
        return 1
    with open(config) as f:
        raw = yaml.safe_load(f)
    print('\n'.join(summary_lines(cfg, raw)))
    errors = cross_check(cfg, raw)
    for e in errors:
        print(f'ERROR: {e}')
    print('INVALID' if errors else 'OK: FleetConfiguration.from_config_files() accepted the '
          'config and all cross-checks passed')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
