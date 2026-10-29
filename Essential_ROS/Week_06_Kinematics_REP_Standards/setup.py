from setuptools import setup

package_name = 'amr_week06'

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
    description='Week 06: differential-drive kinematics and odometry (REP 103/105)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'diff_drive_kinematics = amr_week06.diff_drive_kinematics:main',
            'square_driver = amr_week06.square_driver:main',
        ],
    },
)
