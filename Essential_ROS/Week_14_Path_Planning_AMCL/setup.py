from glob import glob

from setuptools import setup

package_name = 'amr_week14'

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
    description='Week 14: Nav2 bringup with AMCL, NavFn and DWB',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'amcl_initial_pose = amr_week14.amcl_initial_pose:main',
            'nav2_lifecycle_guard = amr_week14.nav2_lifecycle_guard:main',
        ],
    },
)
