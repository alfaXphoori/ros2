"""The dock & charge behavior tree is validated against the INSTALLED Nav2 / docking BT models."""
import os

import pytest
from ament_index_python.packages import get_package_share_directory

from amr_adv03.bt_check import check_tree, docking_models, main, nav2_models, plugin_libs_from_yaml

SHARE = get_package_share_directory('amr_adv03')
BT = os.path.join(SHARE, 'behavior_trees', 'dock_and_charge_bt.xml')
PLUGINS = os.path.join(SHARE, 'config', 'bt_navigator_docking.yaml')

# the tree as it was before the fix
OLD_BT = """<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <Sequence name="DockAndChargeSequence">
      <Condition ID="IsBatteryLow" min_battery="20.0"/>
      <Action ID="NavigateToPose" goal="{staging_pose}"/>
      <Action ID="DockRobot" dock_id="charging_station_01" max_staging_time="15.0"/>
      <Action ID="Wait" wait_duration="30"/>
    </Sequence>
  </BehaviorTree>
</root>"""


@pytest.fixture(scope='module')
def models():
    return nav2_models(), docking_models()


def test_installed_models_are_found(models):
    nav2, docking = models
    for node in ('IsBatteryLow', 'ComputePathToPose', 'FollowPath', 'Wait', 'NavigateToPose'):
        assert node in nav2
    assert 'min_battery' in nav2['IsBatteryLow']
    assert {'dock_id', 'navigate_to_staging_pose', 'use_dock_id'} <= docking['DockRobot'][0]
    assert 'dock_type' in docking['UndockRobot'][0]


def test_module_tree_is_valid(models):
    assert check_tree(BT, plugin_libs_from_yaml(PLUGINS), *models) == []
    assert main([BT, '--plugins-yaml', PLUGINS]) == 0


def test_docking_plugins_must_be_loaded(models):
    errors = check_tree(BT, set(), *models)
    assert any('opennav_dock_action_bt_node' in e for e in errors)
    assert any('opennav_undock_action_bt_node' in e for e in errors)


def test_old_tree_is_rejected(models, tmp_path):
    path = tmp_path / 'old.xml'
    path.write_text(OLD_BT)
    errors = check_tree(str(path), plugin_libs_from_yaml(PLUGINS), *models)
    assert any('BTCPP_format' in e for e in errors)
    assert any('min_battery=20.0' in e for e in errors)  # percentage is 0..1 -> always "low"


def test_typo_in_port_is_rejected(models, tmp_path):
    path = tmp_path / 'typo.xml'
    with open(BT) as f:
        path.write_text(f.read().replace('navigate_to_staging_pose=', 'navigate_to_stage_pose='))
    errors = check_tree(str(path), plugin_libs_from_yaml(PLUGINS), *models)
    assert any('navigate_to_stage_pose' in e for e in errors)
