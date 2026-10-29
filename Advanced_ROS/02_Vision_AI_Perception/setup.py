from glob import glob

from setuptools import setup

package_name = 'amr_adv02'

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
    description='Advanced module 02: synthetic AprilTag camera, AprilTag PnP dock tracker and '
                'a Detection2DArray object detector (classical CV, optional YOLO)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'synthetic_tag_camera = amr_adv02.synthetic_tag_camera:main',
            'apriltag_dock_tracker = amr_adv02.apriltag_dock_tracker:main',
            'object_detector = amr_adv02.object_detector_node:main',
            'pose_error_monitor = amr_adv02.pose_error_monitor:main',
        ],
    },
)
