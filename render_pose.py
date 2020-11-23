import os
import subprocess
import numpy as np

def render(out_dir="./.output/human_pose_x",
           resolution=100,
           samplings=6,
           animation=False,
           pose=None):

    if animation:
        anim_frame_option = "--render-anim"
    else:
        anim_frame_option = "--render-frame 1"

    # Create the output directory
    try:
        os.mkdir("".join(out_dir.split("/")[:-1]))
    except:
        pass
    
    blender_path = "/lhome/sbudara/Documents/blender283/blender"
    script_path = "./single_human_pose.py"

    if os.path.exists(blender_path):
        bashCommand = f"{blender_path} --python {script_path} {anim_frame_option} -- {out_dir} {resolution} {samplings} '{(list(pose))}'"
    else:
        bashCommand = f"blender --python {script_path} {anim_frame_option} -- {out_dir} {resolution} {samplings} '{(list(pose))}'"

    process = subprocess.call(bashCommand, shell=True)
    
if __name__ == "__main__":
    pose = [
        [0,            0,           0],
        [-1.2853e-01,  1.0512e-02, -5.0679e-02],
        [2.7709e-02,  2.5100e-01, -4.0710e-01],
        [1.1463e-02,  6.4020e-01, -1.8854e-01],
        [1.2853e-01, -1.0512e-02,  5.0679e-02],
        [2.5803e-01,  2.2097e-01, -3.2205e-01],
        [1.8305e-01,  6.0340e-01, -1.0381e-01],
        [-1.5258e-02, -2.2694e-01, -3.8681e-02],
        [7.4004e-05, -4.6908e-01, -1.3338e-01],
        [1.4456e-02, -5.1081e-01, -2.3333e-01],
        [2.9278e-03, -6.2335e-01, -2.0242e-01],
        [1.2188e-01, -4.2333e-01, -7.5336e-02],
        [2.8961e-01, -1.9935e-01, -4.9643e-02],
        [2.3501e-01, -1.7183e-01, -2.9430e-01],
        [-1.2729e-01, -4.0671e-01, -1.4703e-01],
        [-2.6958e-01, -1.6512e-01, -1.6593e-01],
        [-1.3282e-01, -8.0722e-02, -3.6027e-01]]

    render(pose=pose)    