import sys
import os
from typing import List, Optional, Tuple, Union

import bpy
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils  # noqa


class Skeleton:
    def __init__(self,
                 joint_coordinates: List[List[float]],
                 joint_connections: Optional[Tuple[Tuple[int, int], ...]] = None,
                 rgb: Tuple[float, float, float] = (0.1, 0.2, 0.6),
                 alpha: float = 1,
                 mettalic: float = 0.5,
                 specular: float = 0.5,
                 roughness: float = 0.9,
                 shadow_on: bool = True,
                 ) -> None:

        self.mettalic = mettalic
        self.specular = specular
        self.roughness = roughness
        self.shadow_on = shadow_on
        self.joint_coordinates = self._standardize(joint_coordinates)
        self.rgba = self._get_rgba(rgb, alpha)
        self.joint_radius = 0.07

        if joint_connections:
            self.joint_connections = joint_connections
        else:
            self.joint_connections = ((0, 7), (7, 8), (8, 9), (9, 10),
                                      (8, 11), (11, 12), (12, 13),
                                      (8, 14), (14, 15), (15, 16), (0, 1),
                                      (1, 2), (2, 3), (0, 4), (4, 5), (5, 6))

        self.joints = self.create_joints()
        self.limbs = self.create_limbs()

    def create_limbs(self) -> List[object]:
        limbs = []
        for idx, connection in enumerate(self.joint_connections):
            draw_curve = bpy.data.curves.new('draw_curve'+str(idx), 'CURVE')
            draw_curve.dimensions = '3D'
            spline = draw_curve.splines.new('BEZIER')
            spline.bezier_points.add(1)
            curve = bpy.data.objects.new('curve'+str(idx), draw_curve)
            bpy.context.collection.objects.link(curve)

            # Curve settings for new curve
            draw_curve.resolution_u = 64
            draw_curve.fill_mode = 'FULL'
            draw_curve.bevel_depth = 0.04
            draw_curve.bevel_resolution = 5

            # Assign bezier points to selection object locations
            for i in range(len(connection)):
                p = spline.bezier_points[i]
                p.co = self.joint_coordinates[connection[i]]
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"

            bpy.context.view_layer.objects.active = curve
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.object.cycles_visibility.shadow = self.shadow_on
            limbs.append(curve)

        return limbs

    def create_joints(self) -> List[object]:
        joint_objs = []

        for x, y, z in self.joint_coordinates:
            obj = utils.create_smooth_sphere(location=(x, y, z),
                                             radius=self.joint_radius)
            joint_objs.append(obj)

        return joint_objs

    @staticmethod
    def _get_rgba(rgb: Tuple[float, float, float], alpha: float):
        # TODO add functionality to convery hex/web to rgb
        # cant use external python pkgs - only blender's python

        # add alpha to the rgb tuple
        rgba = rgb + (alpha,)

        return rgba

    @staticmethod
    def _standardize(coordinates: List[List[float]]) -> np.ndarray:
        coordinates: np.ndarray = np.array(coordinates)

        assert coordinates.shape[-1] == 3, "[x,y,z] values are required"
        assert coordinates.dtype != np.dtype('object'), "2D list not uniform"

        # rearrange data - might not be required for every dataset
        coordinates[:, 1] *= -1
        coordinates = coordinates[:, [0, 2, 1]]

        # scale to unit length
        coordinates = coordinates / np.max(coordinates)

        # make lowest point as origin -> so above floor
        coordinates -= coordinates[coordinates[:, -1].argmin()]

        elevation = 0.1
        coordinates[:, 2] += elevation

        return coordinates
