#!/usr/bin/env python3.7

import os
import sys
import bpy
import math
import numpy as np
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils  # noqa


def set_principled_node_as_rough_blue(principled_node: bpy.types.Node) -> None:
    utils.set_principled_node(
        principled_node=principled_node,
        base_color=(0.1, 0.2, 0.6, 1.0),
        metallic=0.5,
        specular=0.5,
        roughness=0.9,
    )


def set_principled_node_as_rough_red(principled_node: bpy.types.Node) -> None:
    utils.set_principled_node(
        principled_node=principled_node,
        base_color=(0.6, 0.2, 0.1, 1.0),
        metallic=0.5,
        specular=0.5,
        roughness=0.9,
        alpha=0.3,
    )


def set_principled_node_as_ceramic(principled_node: bpy.types.Node) -> None:
    utils.set_principled_node(
        principled_node=principled_node,
        # base_color=(0.8, 0.8, 0.8, 1.0),
        base_color=(1.0, 1.0, 1.0, 1.0),
        subsurface=0.1,
        subsurface_color=(0.9, 0.9, 0.9, 1.0),
        subsurface_radius=(1.0, 1.0, 1.0),
        metallic=0.2,
        specular=0.5,
        roughness=0.0,
    )


def create_custom_material(principled_node_setter, name):
    mat = utils.add_material(
        name, use_nodes=True, make_node_tree_empty=True)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node_setter(principled_node)
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    return mat


def set_floor_and_lights(floor_mat) -> None:
    size = 20.0
    current_object = utils.create_plane(size=size, name="Floor")
    mat = create_custom_material(
        set_principled_node_as_ceramic, "Material_Floor")
    current_object.data.materials.append(mat)

    utils.create_area_light(location=(4.0, -3.0, 6.0),
                            rotation=(0.0, math.pi * 60.0 /
                                      180.0, - math.pi * 32.0 / 180.0),
                            size=0.50,
                            color=(1.00, 1.0, 1.0, 1.00),
                            strength=1500.0,
                            name="Main Light")
#


def set_scene_objects(pose) -> bpy.types.Object:
    mat = create_custom_material(
        set_principled_node_as_rough_blue, "Material_Right")

    skeleton = utils.Skeleton(pose, shadow_on=True)

    for joint in skeleton.joints:
        joint.data.materials.append(mat)

    for limb in skeleton.limbs:
        limb.data.materials.append(mat)

    mat = create_custom_material(
        set_principled_node_as_ceramic, "Material_Plane")
    set_floor_and_lights(mat)

    # camera focus - pelvis or any point, check manually?
    focus_location = (skeleton.joint_coordinates[0][0],
                      skeleton.joint_coordinates[0][1], 
                      skeleton.joint_coordinates[0][2])
    bpy.ops.object.empty_add(location=focus_location)
    focus_target = bpy.context.object
    return focus_target


def render_image():

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
    res_x, res_y = 1080, 1080

    utils.set_output_properties(scene, resolution_percentage, output_file_path,
                                res_x, res_y)

    utils.set_cycles_renderer(scene, camera_object,
                              num_samples, use_transparent_bg=True)


if __name__ == "__main__":
    render_image()
