"""Script to create 3D skeleton given a list of x,y,z coordinates of joints
    Use the script with GUI enabled instead of background and find the desired
    parameters for color, material, camera position, zoom etc
"""

import argparse
import json
import math
import os
import sys
from typing import Callable, List, Tuple

import bpy
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils  # noqa


class Skeleton:
    def __init__(
        self,
        joint_coordinates: List[List[float]],
        joint_links: List[List[int]],
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
            joint_links ([List[List[int, int]]]):
                List of links to draw limbs connecting joints.
            rgb (Tuple[float, float, float], optional): Defaults to (0.1, 0.2, 0.6).
            alpha (float, optional): Transparency of whole skeleton. Defaults to 1.
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
        self.rgba = rgb + (alpha,)
        self.joint_radius = 0.07
        self.joint_links = joint_links

        self.joints = self.create_joints()
        self.limbs = self.create_limbs()

        # TODO make different set_principled_node to use different materials
        set_materials(self.joints, self.set_principled_node_skeleton, "Material_Joints")
        set_materials(self.limbs, self.set_principled_node_skeleton, "Material_Limbs")

    def create_limbs(self) -> List[object]:
        """Blender objects for limbs - Splines."""
        limbs = []
        for idx, connection in enumerate(self.joint_links):
            draw_curve = bpy.data.curves.new("draw_curve" + str(idx), "CURVE")
            draw_curve.dimensions = "3D"
            spline = draw_curve.splines.new("BEZIER")
            spline.bezier_points.add(1)
            curve = bpy.data.objects.new("curve" + str(idx), draw_curve)
            bpy.context.collection.objects.link(curve)

            # Curve settings for new curve
            draw_curve.resolution_u = 64
            draw_curve.fill_mode = "FULL"
            draw_curve.bevel_depth = 0.04
            draw_curve.bevel_resolution = 5

            # Assign bezier points to selection object locations
            for i in range(len(connection)):
                p = spline.bezier_points[i]
                p.co = self.joint_coordinates[connection[i]]
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"

            bpy.context.view_layer.objects.active = curve
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.context.object.cycles_visibility.shadow = self.shadow_on
            limbs.append(curve)

        return limbs

    def create_joints(self) -> List[object]:
        """Blender objects for joint - Spheres."""
        joint_objs = []

        for x, y, z in self.joint_coordinates:
            obj = utils.create_smooth_sphere(location=(x, y, z), radius=self.joint_radius)
            joint_objs.append(obj)

        return joint_objs

    def set_principled_node_skeleton(self, principled_node: bpy.types.Node) -> None:
        """sets required properties for the particular material."""
        utils.set_principled_node(
            principled_node=principled_node,
            base_color=self.rgba,
            metallic=self.metallic,
            specular=self.specular,
            roughness=self.roughness,
        )

    @staticmethod
    def _standardize(joint_coordinates: List[List[float]]) -> np.ndarray:
        """Standardize all poses to certain range for consistency with camera angle, floor, zoom etc."""
        coordinates: np.ndarray = np.array(joint_coordinates)

        assert coordinates.shape[-1] == 3, "[x,y,z] values are required"
        assert coordinates.dtype != np.dtype("object"), "2D list not uniform"

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
        self.base_color = (1.0, 1.0, 1.0, 1.0)
        self.subsurface = 0.1
        self.subsurface_color = (0.9, 0.9, 0.9, 1.0)
        self.subsurface_radius = (1.0, 1.0, 1.0)
        self.metallic = 0.2
        self.specular = 0.5
        self.roughness = 0.0

        self.plane = utils.create_plane(size=self.size, name="Floor")
        set_materials([self.plane], self.set_principled_node_floor, "Material_Floor")

    def set_principled_node_floor(self, principled_node: bpy.types.Node) -> None:
        utils.set_principled_node(
            principled_node=principled_node,
            base_color=self.base_color,
            subsurface=self.subsurface,
            subsurface_color=self.subsurface_color,
            subsurface_radius=self.subsurface_radius,
            metallic=self.metallic,
            specular=self.specular,
            roughness=self.roughness,
        )


def set_materials(objects: List[object], principled_node_setter: Callable, name: str) -> None:
    mat = utils.add_material(name, use_nodes=True, make_node_tree_empty=True)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_node_setter(principled_node)
    links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

    for obj in objects:
        obj.data.materials.append(mat)


def parse_arguments():
    # Get args following the separator between blender args and python args
    argv = None
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]

    parser = argparse.ArgumentParser()
    parser.add_argument("--pose", type=str)
    parser.add_argument("--joint_links", type=str)
    parser.add_argument("--color", type=float, nargs=3)
    parser.add_argument("--gt_pose", type=str)
    parser.add_argument("--gt_joint_links", type=str)
    parser.add_argument("--gt_color", type=float, nargs=3)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--resolution_percentage", type=int)
    parser.add_argument("--samplings", type=int)

    # Only parse python args
    args = parser.parse_known_args(argv)[0]
    return args


def render_image():
    """The method invoked by blender cli that renders the output image."""

    # Args
    args = parse_arguments()
    args.color = tuple(args.color)
    args.gt_color = tuple(args.gt_color)

    # Load poses from JSON strings
    pose = np.array(json.loads(args.pose))
    joint_links = np.array(json.loads(args.joint_links))
    gt_pose = np.array(json.loads(args.gt_pose)) if args.gt_pose else None
    gt_joint_links = np.array(json.loads(args.gt_joint_links)) if args.gt_joint_links else None

    # Scene Building
    scene = bpy.data.scenes["Scene"]
    world = scene.world

    # Reset
    utils.clean_objects()

    # Create all objects
    assert len(args.color) == 3
    skeleton = Skeleton(pose, joint_links, shadow_on=True, rgb=args.color)
    if gt_pose is not None:
        assert len(args.gt_color) == 3
        if gt_joint_links is None:
            raise ValueError("GT joint link must be passed along with pose.")
        _ = Skeleton(gt_pose, gt_joint_links, shadow_on=True, rgb=args.gt_color)

    _ = Floor(size=20.0)

    # Lighting based on asset
    # hdri_path = "./assets/HDRIs/green_point_park_2k.hdr"
    # utils.build_environment_texture_background(world, hdri_path)

    # Custom Light
    utils.create_area_light(
        location=(4.0, -3.0, 6.0),
        rotation=(0.0, math.pi * 60.0 / 180.0, -math.pi * 32.0 / 180.0),
        size=0.50,
        color=(1.00, 1.0, 1.0, 1.00),
        strength=1500.0,
        name="Main Light",
    )

    # camera focus - pelvis or any point. Could check manually to verify best placing.
    focus_location = (
        skeleton.joint_coordinates[0][0],
        skeleton.joint_coordinates[0][1],
        skeleton.joint_coordinates[0][2],
    )
    bpy.ops.object.empty_add(location=focus_location)
    focus_target = bpy.context.object

    # Camera
    bpy.ops.object.camera_add(location=(0.0, -8.0, 2.0))
    camera_object = bpy.context.object

    utils.add_track_to_constraint(camera_object, focus_target)
    utils.set_camera_params(camera_object.data, focus_target, lens=85, fstop=0.5)

    # Background
    utils.build_rgb_background(world, rgb=(1.0, 1.0, 1.0, 1.0))

    # Render Setting
    res_x, res_y = 1080, 1080

    utils.set_output_properties(scene, args.resolution_percentage, args.output_path, res_x, res_y)

    utils.set_cycles_renderer(scene, camera_object, args.samplings, use_transparent_bg=True)


if __name__ == "__main__":
    render_image()
