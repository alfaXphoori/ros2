from setuptools import setup

package_name = 'amr_week08'

setup(
    name=package_name,
    version='1.0.0',
    # The exam's reference solution lives in solution/ (mirrors a student submission folder)
    package_dir={package_name: 'solution'},
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/urdf', ['solution/hospital_amr.urdf']),
        ('share/' + package_name + '/launch', ['solution/hospital_bringup.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Phoori Chantima',
    maintainer_email='phoori.ch@ksu.ac.th',
    description='Week 08 midterm exam: reference solution and autograder',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hospital_robot_node = amr_week08.hospital_robot_node:main',
        ],
    },
)
