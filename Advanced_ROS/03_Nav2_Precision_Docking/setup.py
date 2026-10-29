from glob import glob

from setuptools import setup

package_name = 'amr_adv03'

setup(
    name=package_name,
    version='1.0.0',
    package_dir={package_name: 'src'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/behavior_trees', glob('behavior_trees/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Advanced module 03: Nav2 docking server (opennav_docking) with a fake base and '
                'AprilTag detection in the loop, DockRobot/UndockRobot client, dock & charge BT',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fake_base = amr_adv03.fake_base:main',
            'dock_client = amr_adv03.dock_client:main',
            'check_bt = amr_adv03.bt_check:main',
        ],
    },
)
