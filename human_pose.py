# blender --background --python 04_principled_bsdf.py --render-frame 1 -- </path/to/output/image> <resolution_percentage> <num_samples>

import bpy
import sys
import math
import os
import numpy as np
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils
import external.cc0assetsloader as loader

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
        base_color=(0.8, 0.8, 0.8, 1.0),
        subsurface=0.1,
        subsurface_color=(0.9, 0.9, 0.9, 1.0),
        subsurface_radius=(1.0, 1.0, 1.0),
        metallic=0.2,
        specular=0.5,
        roughness=0.0,
    )


def create_pose_objects(pose, shadow=True):
    pose[:, 1] *= -1
    pose = pose[:, [0, 2, 1]]

    js = ('Pelvis', 'R_Hip', 'R_Knee', 'R_Ankle', 'L_Hip', 'L_Knee', 'L_Ankle', 'Torso',
          'Neck', 'Nose', 'Head', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'R_Shoulder', 'R_Elbow', 'R_Wrist')
    skeleton = ((0, 7), (7, 8), (8, 9), (9, 10), (8, 11), (11, 12), (12, 13),
                (8, 14), (14, 15), (15, 16), (0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6))

    head2neck = np.linalg.norm(
        pose[js.index('Head'), :] - pose[js.index('Neck'), :],  keepdims=True)
    neck2torso = np.linalg.norm(
        pose[js.index('Neck'), :] - pose[js.index('Torso'), :],  keepdims=True)
    torso2root = np.linalg.norm(
        pose[js.index('Torso'), :] - pose[js.index('Pelvis'), :],  keepdims=True)
    dist = head2neck+neck2torso + torso2root

    pose -= pose[pose[:, -1].argmin()]
    pose *= 2
    pose[:, 2] += 0.1

    joints = []
    for joint in pose:
        object = utils.create_smooth_sphere(location=(joint[0], joint[1], joint[2]),
                                            radius=0.07, shadow=shadow)
        joints.append(object)

    lines = []
    for idx, line in enumerate(skeleton):

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
        for i in range(len(line)):
            p = spline.bezier_points[i]
            p.co = pose[line[i]]
            p.handle_right_type = "VECTOR"
            p.handle_left_type = "VECTOR"

        bpy.context.view_layer.objects.active = curve
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.cycles_visibility.shadow = shadow
        lines.append(curve)

    return joints, lines

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

def set_scene_objects(pose) -> bpy.types.Object:
    loader.build_pbr_textured_nodes_from_name("Marble01")

    mat = create_custom_material(set_principled_node_as_rough_blue ,"Material_Right")

    if len(pose) == 2:
        # support having ground truth comparision
        mat1 = create_custom_material(set_principled_node_as_rough_red ,"Material_left")
        mats = [mat, mat1]
    else:
        mats = [mat]
        # pose = [pose]
        # debug
        pose = [pose, pose+pose*0.1]
        mat1 = create_custom_material(set_principled_node_as_rough_red ,"Material_left")
        mats = [mat, mat1]

    for idx, (pose_, mat) in enumerate(zip(pose, mats)):
        # ignore ground truth for shadow

        shadow = False if idx==1 else True
        joints, lines = create_pose_objects(pose_, shadow)

        for joint in joints:
            joint.data.materials.append(mat)

        for line in lines:
            line.data.materials.append(mat)
                
    ##################
    mat = create_custom_material(set_principled_node_as_ceramic, "Material_Plane")
    current_object = utils.create_plane(size=20.0, name="Floor")
    current_object.data.materials.append(mat)

    current_object = utils.create_plane(size=12.0,
                                        location=(0.0, 4.0, 0.0),
                                        rotation=(math.pi * 90.0 / 180.0, 0.0, 0.0),
                                        name="Wall")
    current_object.data.materials.append(mat)

    bpy.ops.object.empty_add(location=(0.0, -0.75, 1.3))
    focus_target = bpy.context.object
    return focus_target


def render_image():

    # Args
    output_file_path = str(sys.argv[sys.argv.index('--') + 1])
    resolution_percentage = int(sys.argv[sys.argv.index('--') + 2])
    num_samples = int(sys.argv[sys.argv.index('--') + 3])
    pose_string = sys.argv[sys.argv.index('--') + 4]
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

    # Lights
    utils.build_environment_texture_background(world, hdri_path)

    # Composition
    utils.build_scene_composition(scene)

    # Note 
    bpy.context.scene.name = "MPJPE - 40mm"

    bpy.context.scene.render.use_stamp = True
    bpy.context.scene.render.use_stamp_scene = True
    bpy.context.scene.render.use_stamp_labels = False
    bpy.context.scene.render.use_stamp_memory = False
    bpy.context.scene.render.use_stamp_time = False
    bpy.context.scene.render.use_stamp_date = False
    bpy.context.scene.render.use_stamp_render_time = False
    bpy.context.scene.render.use_stamp_filename = False
    bpy.context.scene.render.use_stamp_frame = False
    bpy.context.scene.render.use_stamp_camera = False
    bpy.context.scene.render.stamp_background = (0, 0, 0, 0)

    bpy.context.scene.render.stamp_font_size = 20
    bpy.context.scene.render.stamp_foreground = (0.8, 0.0243016, 0.0716732, 1)


    # Render Setting
    utils.set_output_properties(scene, resolution_percentage, output_file_path,
                                res_x=1080, res_y=1080)
    
    utils.set_cycles_renderer(scene, camera_object, num_samples)

if __name__ == "__main__":
    render_image()
