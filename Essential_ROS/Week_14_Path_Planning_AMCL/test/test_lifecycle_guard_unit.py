"""Unit tests for the Nav2 lifecycle guard decision logic (no ROS graph)."""

import ast
import os

from amr_week14.nav2_lifecycle_guard import (LOCALIZATION_NODES, NAV2_NODES, NAVIGATION_NODES,
                                             node_to_heal, transitions_for)
from lifecycle_msgs.msg import Transition

LAUNCH = os.path.join(os.path.dirname(__file__), '..', 'launch', 'nav2_bringup.launch.py')


def states(**kw):
    s = {n: 'active' for n in NAV2_NODES}
    s.update(kw)
    return s


def test_nothing_to_heal_when_all_active():
    assert node_to_heal(states(), waited=500.0, heal_after=25.0) is None


def test_waits_for_heal_after_before_touching_localization():
    s = states(amcl='inactive')
    assert node_to_heal(s, waited=24.0, heal_after=25.0) is None
    assert node_to_heal(s, waited=26.0, heal_after=25.0) == 'amcl'


def test_navigation_servers_get_twice_the_time():
    s = states(planner_server='unconfigured')
    assert node_to_heal(s, waited=40.0, heal_after=25.0) is None
    assert node_to_heal(s, waited=51.0, heal_after=25.0) == 'planner_server'


def test_transitional_and_missing_states_are_never_touched():
    for label in ('configuring', 'activating', 'unavailable', 'finalized'):
        assert node_to_heal(states(amcl=label), waited=500.0, heal_after=25.0) is None


def test_each_node_healed_once_in_manager_order():
    s = states(controller_server='unconfigured', smoother_server='unconfigured')
    assert node_to_heal(s, 100.0, 25.0) == 'controller_server'
    assert node_to_heal(s, 100.0, 25.0, healed=['controller_server']) == 'smoother_server'
    assert node_to_heal(s, 100.0, 25.0,
                        healed=['controller_server', 'smoother_server']) is None


def test_transitions_to_active():
    assert transitions_for('unconfigured') == [Transition.TRANSITION_CONFIGURE,
                                               Transition.TRANSITION_ACTIVATE]
    assert transitions_for('inactive') == [Transition.TRANSITION_ACTIVATE]
    assert transitions_for('active') == []
    assert transitions_for('finalized') == []


def test_launch_uses_the_guard_node_lists():
    """nav2_bringup.launch.py must take node_names from the guard, so the lists cannot drift."""
    tree = ast.parse(open(LAUNCH).read())
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                and n.module == 'amr_week14.nav2_lifecycle_guard' for a in n.names}
    assert {'LOCALIZATION_NODES', 'NAVIGATION_NODES'} <= imported
    assert NAV2_NODES == LOCALIZATION_NODES + NAVIGATION_NODES
    assert len(set(NAV2_NODES)) == 10
