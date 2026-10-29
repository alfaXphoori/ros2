from glob import glob

from setuptools import setup

package_name = 'amr_week09'

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
    description='Week 09: TF2 static broadcaster and listener',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'static_sensor_broadcaster = amr_week09.static_sensor_broadcaster:main',
            'tf_obstacle_listener = amr_week09.tf_obstacle_listener:main',
        ],
    },
)
