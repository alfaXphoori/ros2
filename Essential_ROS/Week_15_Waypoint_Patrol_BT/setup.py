from glob import glob

from setuptools import setup

package_name = 'amr_week15'

setup(
    name=package_name,
    version='1.0.0',
    package_dir={package_name: 'src'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/behavior_trees', glob('behavior_trees/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Week 15: Nav2 waypoint patrol and custom behavior tree',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'waypoint_patrol = amr_week15.waypoint_patrol:main',
        ],
    },
)
