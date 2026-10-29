from setuptools import setup

package_name = 'amr_week02'

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
    description='Week 02: nodes, topics and QoS policies',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sensor_qos_publisher = amr_week02.sensor_qos_publisher:main',
            'sensor_qos_subscriber = amr_week02.sensor_qos_subscriber:main',
        ],
    },
)
