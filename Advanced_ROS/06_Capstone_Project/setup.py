from glob import glob

from setuptools import setup

package_name = 'amr_adv06'

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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Advanced module 06: integrated headless warehouse AMR capstone '
                '(Gazebo + Nav2 + collision monitor + docking + AprilTag) with a KPI-measuring '
                'mission executor',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ground_truth_tf = amr_adv06.ground_truth_tf:main',
            'capstone_mission = amr_adv06.capstone_mission:main',
            'plot_capstone = amr_adv06.plot_capstone:main',
            'kidnap_demo = amr_adv06.kidnap_demo:main',
        ],
    },
)
