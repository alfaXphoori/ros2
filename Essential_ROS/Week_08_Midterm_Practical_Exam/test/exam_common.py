"""Shared helpers for the Week 08 midterm autograder.

The grader checks the folder given by the environment variable EXAM_SUBMISSION_DIR
(default: ../solution, the reference solution). A submission folder must contain:
  hospital_amr.urdf, hospital_robot_node.py, hospital_bringup.launch.py
"""
import math
import os
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SUBMISSION_DIR = os.path.abspath(os.environ.get(
    'EXAM_SUBMISSION_DIR', os.path.join(HERE, '..', 'solution')))
URDF_PATH = os.path.join(SUBMISSION_DIR, 'hospital_amr.urdf')
NODE_PATH = os.path.join(SUBMISSION_DIR, 'hospital_robot_node.py')
LAUNCH_PATH = os.path.join(SUBMISSION_DIR, 'hospital_bringup.launch.py')

NODE_NAME = 'midterm_robot_controller'


def rpy_to_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rz @ ry @ rx


def vec(text, default='0 0 0'):
    return np.array([float(v) for v in (text or default).split()])


def origin_of(elem):
    o = elem.find('origin') if elem is not None else None
    if o is None:
        return np.zeros(3), np.eye(3)
    return vec(o.get('xyz')), rpy_to_matrix(*vec(o.get('rpy')))


class UrdfModel:
    """Minimal URDF reader: links, joints and link poses at zero joint angles."""

    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.links = {link.get('name'): link for link in self.root.findall('link')}
        self.joints = {j.get('name'): j for j in self.root.findall('joint')}
        self.joint_of_child = {j.find('child').get('link'): j for j in self.joints.values()}
        self._poses = {}

    def pose(self, link, root='base_footprint'):
        """(position, rotation) of `link` expressed in `root`."""
        if link == root:
            return np.zeros(3), np.eye(3)
        key = (link, root)
        if key not in self._poses:
            j = self.joint_of_child[link]
            pp, pr = self.pose(j.find('parent').get('link'), root)
            xyz, rot = origin_of(j)
            self._poses[key] = (pp + pr @ xyz, pr @ rot)
        return self._poses[key]

    def mass(self, link):
        return float(self.links[link].find('inertial/mass').get('value'))

    def inertia_in_link_frame(self, link):
        inertial = self.links[link].find('inertial')
        i = inertial.find('inertia')
        g = {k: float(i.get(k, 0.0)) for k in ('ixx', 'iyy', 'izz', 'ixy', 'ixz', 'iyz')}
        tensor = np.array([[g['ixx'], g['ixy'], g['ixz']],
                           [g['ixy'], g['iyy'], g['iyz']],
                           [g['ixz'], g['iyz'], g['izz']]])
        _, rot = origin_of(inertial)
        return rot @ tensor @ rot.T

    def geometry(self, link, shape):
        return self.links[link].find(f'collision/geometry/{shape}')

    def box_extent_z(self, link):
        """(bottom, top) z of a link's collision box, expressed in base_footprint."""
        size = vec(self.geometry(link, 'box').get('size'))
        xyz, _ = origin_of(self.links[link].find('collision'))
        z = self.pose(link)[0][2] + xyz[2]
        return z - size[2] / 2, z + size[2] / 2
