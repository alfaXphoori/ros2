from glob import glob

from setuptools import setup

package_name = 'amr_week16'

setup(
    name=package_name,
    version='1.0.0',
    package_dir={package_name: 'src'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Week 16: final demonstration bringup and mission executor',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'final_mission_executor = amr_week16.final_mission_executor:main',
            'record_path = amr_week16.mission_path:record_main',
            'plot_path = amr_week16.mission_path:plot_main',
        ],
    },
)
