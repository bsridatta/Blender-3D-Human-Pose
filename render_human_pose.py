import subprocess
from typing import Optional


def render_pose(
    pose: list[list[float]],
    color: tuple[float, float, float] = (0.1, 0.2, 0.6),
    gt_pose: Optional[list[list[float]]] = None,
    gt_color: Optional[tuple[float, float, float]] = (0.6, 0.2, 0.1),
    output_path: str = "./output/pose",
    resolution_percentage: int = 100,
    samplings: int = 128,
    blender_path: str = "blender",
    gui: bool = False,
):
    """The method to use from your project to render poses.
    Calls this script with required args using blender cli.

    Args:
        pose (list[list[float]]): List of x,y,z, of joints.
        color (tuple[float, float, float], optional): RGB (0-1 scale) color for skeleton. Defaults to (0.1, 0.2, 0.6).
        gt_pose (Optional[list[list[float]]], optional): Pose for comparison. Defaults to None.
        gt_color (Optional[tuple[float, float, float]], optional): RGB (0-1 scale) for GT skeleton. Defaults to (0.6, 0.2, 0.1).
        output_path (str, optional): Save dir path or file name. Defaults to "./output/pose".
        resolution_percentage (int, optional): Percentage of resolution (1080). Defaults to 100.
        samplings (int, optional): Samples during rendering. Defaults to 128.
        blender_path (str, optional): Blender exec path. Defaults to "blender".
        gui (bool, optional): Run with gui, for experimentation and debugging. Defaults to False.
    """
    script_path = "human_pose.py"
    cmd_parts = [
        blender_path,
        "--background" if not gui else "",
        f"--python {script_path}",
        "--render-frame 1",
        "--",  # Blender ignore the args following this.
        f"--pose '{(list(pose))}'",
        f"--color {color[0]} {color[1]} {color[2]}" if color else "",
        f"--gt_pose '{(list(gt_pose))}'" if gt_pose is not None else "",
        f"--gt_color {gt_color[0]} {gt_color[1]} {gt_color[2]}" if gt_color else "",
        f"--output_path {output_path}",
        f"--resolution_percentage {resolution_percentage}",
        f"--samplings {samplings}",
    ]
    command = " ".join(cmd_parts)
    _ = subprocess.call(command, shell=True)
