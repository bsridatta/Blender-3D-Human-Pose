"""Script to create 3D skeleton given a list of x,y,z coordinates of joints
    Use the script with GUI enabled instead of background and find the desired
    parameters for color, material, camera position, zoom etc
"""

import json
import math
import os
import subprocess
import sys
from typing import Callable, List, Optional, Tuple

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
                 metallic: float = 0.5,
                 specular: float = 0.5,
                 roughness: float = 0.9,
                 shadow_on: bool = True,
                 ) -> None:
        """Blender object collection for a 3D pose/skeleton

        Args:
            joint_coordinates (List[List[float]]): x,y,z of all joints
            joint_connections (Optional[Tuple[Tuple[int, int], ...]], optional): 
                Tuples of links to draw limbs connecting joints. Defaults to None.
            rgb (Tuple[float, float, float], optional): Defaults to (0.1, 0.2, 0.6).
            alpha (float, optional): Transperancy of whole skeleton. Defaults to 1.
            metallic (float, optional): Defaults to 0.5.
            specular (float, optional): Defaults to 0.5.
            roughness (float, optional): Defaults to 0.9.
            shadow_on (bool, optional): Enable shadows of skeleton. Defaults to True.
        """
        self.metallic = metallic
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

        # TODO make different set_principled_node to use different materials
        set_materials(
            self.joints, self.set_principled_node_skeleton, "Material_Joints")
        set_materials(
            self.limbs, self.set_principled_node_skeleton, "Material_Limbs")

    def create_limbs(self) -> List[object]:
        """Blender objects for limbs - Splines
        """
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
        """Blender objects for joint - Speheres
        """
        joint_objs = []

        for x, y, z in self.joint_coordinates:
            obj = utils.create_smooth_sphere(location=(x, y, z),
                                             radius=self.joint_radius)
            joint_objs.append(obj)

        return joint_objs

    def set_principled_node_skeleton(self, principled_node: bpy.types.Node) -> None:
        """sets required properites for the particular material
        """
        utils.set_principled_node(
            principled_node=principled_node,
            base_color=self.rgba,
            metallic=self.metallic,
            specular=self.specular,
            roughness=self.roughness,
        )

    @staticmethod
    def _get_rgba(rgb: Tuple[float, float, float], alpha: float):
        # TODO add functionality to convery hex/web to rgb
        # cant use external python pkgs - only blender's python

        # add alpha to the rgb tuple
        rgba = rgb + (alpha,)
        return rgba

    @staticmethod
    def _standardize(joint_coordinates: List[List[float]]) -> np.ndarray:
        """Standardize all poses to certain range for consistency with camera angle, floor, zoom etc
        """
        coordinates: np.ndarray = np.array(joint_coordinates)

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


class Floor:
    def __init__(self, size) -> None:
        self.size = size
        # self.base_color=(0.8, 0.8, 0.8, 1.0)
        self.base_color = (1.0, 1.0, 1.0, 1.0)
        self.subsurface = 0.1
        self.subsurface_color = (0.9, 0.9, 0.9, 1.0)
        self.subsurface_radius = (1.0, 1.0, 1.0)
        self.metallic = 0.2
        self.specular = 0.5
        self.roughness = 0.0
        
        self.plane = utils.create_plane(size=self.size, name="Floor")
        set_materials([self.plane], self.set_principled_node_floor,
                      "Material_Floor")

    def set_principled_node_floor(self, principled_node: bpy.types.Node) -> None:
        utils.set_principled_node(
            principled_node=principled_node,
            # base_color=self.base_color,
            base_color=self.base_color,
            subsurface=self.subsurface,
            subsurface_color=self.subsurface_color,
            subsurface_radius=self.subsurface_radius,
            metallic=self.metallic,
            specular=self.specular,
            roughness=self.roughness
        )


def set_materials(objects: List[object], principled_node_setter: Callable, name: str) -> None:
    mat = utils.add_material(
        name, use_nodes=True, make_node_tree_empty=True)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node_setter(principled_node)
    links.new(principled_node.outputs['BSDF'],
              output_node.inputs['Surface'])

    for obj in objects:
        obj.data.materials.append(mat)


def set_scene_objects(pose) -> bpy.types.Object:
    """creates all objects in the scene. 
    Pose skeleton, floor, lights, focus object for camera to focus at.

    """
    skeleton = Skeleton(pose, shadow_on=True)
    
    floor = Floor(size=20.0)

    utils.create_area_light(location=(4.0, -3.0, 6.0),
                            rotation=(0.0, math.pi * 60.0 /
                                      180.0, - math.pi * 32.0 / 180.0),
                            size=0.50,
                            color=(1.00, 1.0, 1.0, 1.00),
                            strength=1500.0,
                            name="Main Light")

    # camera focus - pelvis or any point, check manually?
    focus_location = (skeleton.joint_coordinates[0][0],
                      skeleton.joint_coordinates[0][1],
                      skeleton.joint_coordinates[0][2])

    bpy.ops.object.empty_add(location=focus_location)
    focus_target = bpy.context.object
    return focus_target


def render_image():
    """The method invoked by blender cli that renders the output image
    """

    # Args
    output_file_path = str(sys.argv[sys.argv.index('--') + 1])
    resolution_percentage = int(sys.argv[sys.argv.index('--') + 2])
    num_samples = int(sys.argv[sys.argv.index('--') + 3])
    color = int(sys.argv[sys.argv.index('--') + 4])
    pose_string = sys.argv[sys.argv.index('--') + 5]
    pose = np.array(json.loads(pose_string))

    # Parameters
    hdri_path = "./assets/HDRIs/green_point_park_2k.hdr"

    # Scene Building
    scene = bpy.data.scenes["Scene"]
    world = scene.world

    # Reset
    utils.clean_objects()

    # Objects
    focus_target = set_scene_objects(pose)

    # Camera
    bpy.ops.object.camera_add(location=(0.0, -8.0, 2.0))
    camera_object = bpy.context.object

    utils.add_track_to_constraint(camera_object, focus_target)
    utils.set_camera_params(
        camera_object.data, focus_target, lens=85, fstop=0.5)

    # Background
    utils.build_rgb_background(world, rgb=(1.0, 1.0, 1.0, 1.0))

    # Render Setting
    # TODO get as arg
    res_x, res_y = 1080, 1080

    utils.set_output_properties(scene, resolution_percentage, output_file_path,
                                res_x, res_y)

    utils.set_cycles_renderer(scene, camera_object,
                              num_samples, use_transparent_bg=True)


def render_pose(pose=None,
                color=0,
                gt=None,
                error=0,
                out_dir="./output/pose",
                resolution=100,
                samplings=128,
                animation=False,
                blender_path='blender'):
    """The method to use from your project to render poses. 
    Calls this script with requried args using blender cli. 


    Args:
        pose ([type], optional): List of x,y,z, of joints. Defaults to None.
        color (int, optional): Color for skeleton. Defaults to 0.
        gt ([type], optional): GT pose for comparision. Not implemented. Defaults to None.
        error (int, optional): Show error on render. Not implemented. Defaults to 0.
        out_dir (str, optional): save dir path or file name. Defaults to "./output/pose".
        resolution (int, optional): percentage of resolution (1080). Defaults to 100.
        samplings (int, optional): samples during rendering. Defaults to 128.
        animation (bool, optional): not implemented. Defaults to False.
        blender_path (str, optional): blender exec path. Defaults to 'blender'.
    """

    if animation:
        anim_frame_option = "--render-anim"
    else:
        anim_frame_option = "--render-frame 1"

    script_path = "human_pose.py"

    if not gt:
        bashCommand = f"{blender_path} --background --python {script_path} \
            {anim_frame_option} -- \
            {out_dir} {resolution} {samplings} {color} '{(list(pose))}'"
    else:
        bashCommand = f"{blender_path} --background --python {script_path} \
            {anim_frame_option} -- \
            {out_dir} {resolution} {samplings} {color} '{(list(pose))}' \
            '{(list(gt))}' '{error}'"

    process = subprocess.call(bashCommand, shell=True)


if __name__ == "__main__":
    render_image()
