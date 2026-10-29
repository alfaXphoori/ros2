from setuptools import setup

package_name = 'amr_week03'

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
    description='Week 03: services, clients and the executor deadlock trap',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'power_service_server = amr_week03.power_service_server:main',
            'power_service_client = amr_week03.power_service_client:main',
            'deadlock_demo = amr_week03.deadlock_demo:main',
        ],
    },
)
