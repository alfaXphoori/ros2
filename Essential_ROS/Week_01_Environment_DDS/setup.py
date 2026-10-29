from setuptools import setup

package_name = 'amr_week01'

setup(
    name=package_name,
    version='1.0.0',
    package_dir={package_name: 'src'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Shell script installed next to the console scripts -> `ros2 run amr_week01 domain_check.sh`
        ('lib/' + package_name, ['src/domain_check.sh']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Week 01: ROS 2 environment and DDS/RTPS port diagnostics',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': []},
)
