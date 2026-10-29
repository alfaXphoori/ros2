from setuptools import setup

package_name = 'amr_adv05'

setup(
    name=package_name,
    version='1.0.0',
    package_dir={package_name: 'src'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Advanced 05: lifecycle LaserScan node, launch_testing and SROS2 lab',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lifecycle_laser_sensor = amr_adv05.lifecycle_laser_sensor:main',
        ],
    },
)
