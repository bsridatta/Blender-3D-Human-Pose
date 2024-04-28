# Blender Pose
## 3D Human Pose rendering in Blender
This repo provides a [module](./human_pose.py) to visualize 3D human pose. This module is built upon the utilities from [yuki-koyama/blender-cli-rendering](https://github.com/yuki-koyama/blender-cli-rendering) and currently supports rendering a single pose and optionally a second one (ground truth) for comparison.

This module could serve as an example on how to customize the material, background etc., or further extended to render a grid of poses with finer control over camera and lighting positions. Please share if that is something you would like to see supported here. Use the script with GUI enabled instead of background and find the desired parameters for color, material, camera position, zoom etc.

Refer to the main repo or `other_examples` for working with other objects and rendering techniques.

![GitHub](https://img.shields.io/github/license/yuki-koyama/blender-cli-rendering)
![Blender](https://img.shields.io/badge/blender-2.83-brightgreen)

## Usage
- Blender 2.83 is required
- Invoke the pose rendering method without GUI
- All you need is list of 3D coordinates of the joints

[Render pose](./render_human_pose.py) is a helper function that runs [human pose](./human_pose.py) script in blender and save the rendered images to disk.

```python
def render_pose(
    pose: list[list[float]],
    joint_links: list[list[int]],
    color: tuple[float, float, float] = (0.1, 0.2, 0.6),
    gt_pose: Optional[list[list[float]]] = None,
    gt_joint_links: Optional[list[list[int]]] = None,
    gt_color: Optional[tuple[float, float, float]] = (0.6, 0.1, 0.2),
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
        joint_links (list[list[int]]): List of connections between joints.
        color (tuple[float, float, float], optional): RGB (0-1 scale) color for skeleton. Defaults to (0.1, 0.2, 0.6).
        gt_pose (Optional[list[list[float]]], optional): Pose for comparison. Defaults to None.
        gt_joint_links (Optional[list[list[int]]]): List of connections between joints for GT pose, probably same as `joint_links`.
        gt_color (Optional[tuple[float, float, float]], optional): RGB (0-1 scale) for GT skeleton. Defaults to (0.6, 0.1, 0.2).
        output_path (str, optional): Save dir path or file name. Defaults to "./output/pose".
        resolution_percentage (int, optional): Percentage of resolution (1080). Defaults to 100.
        samplings (int, optional): Samples during rendering. Defaults to 128.
        blender_path (str, optional): Blender exec path. Defaults to "blender".
        gui (bool, optional): Run with gui, for experimentation and debugging. Defaults to False.
    """
```
`blender` may not be added to path. For Mac, the path could be `/Applications/Blender.app/Contents/MacOS/Blender`.

### Simple 3D pose

```python
from render_human_pose import render_pose

pose = [
    [0, 0, 0],
    [-0.1285, 0.0105, -0.0507],
    [0.0277, 0.251, -0.4071],
    [0.0115, 0.6402, -0.1885],
    [0.1285, -0.0105, 0.0507],
    [0.258, 0.221, -0.3221],
    [0.183, 0.6034, -0.1038],
    [-0.0153, -0.2269, -0.0387],
    [0.0001, -0.4691, -0.1334],
    [0.0145, -0.5108, -0.2333],
    [0.0029, -0.6233, -0.2024],
    [0.1219, -0.4233, -0.0753],
    [0.2896, -0.1993, -0.0496],
    [0.235, -0.1718, -0.2943],
    [-0.1273, -0.4067, -0.147],
    [-0.2696, -0.1651, -0.1659],
    [-0.1328, -0.0807, -0.3603],
]

joint_links = [
    [0, 7],
    [7, 8],
    [8, 9],
    [9, 10],
    [8, 11],
    [11, 12],
    [12, 13],
    [8, 14],
    [14, 15],
    [15, 16],
    [0, 1],
    [1, 2],
    [2, 3],
    [0, 4],
    [4, 5],
    [5, 6],
]

render_pose(pose=pose, joint_links=joint_links)
```
<img src="output/single_pose.png">

### Compare poses (prediction vs ground truth)

```python
gt_pose = [
    [0, 0, 0],
    [-0.1284, -0.012, -0.0507],
    [-0.0163, 0.252, -0.4071],
    [-0.0999, 0.6325, -0.1885],
    [0.1284, 0.012, 0.0507],
    [0.2157, 0.2624, -0.3221],
    [0.0755, 0.626, -0.1038],
    [0.0244, -0.2261, -0.0387],
    [0.0815, -0.4619, -0.1334],
    [0.1029, -0.5005, -0.2333],
    [0.1111, -0.6134, -0.2024],
    [0.1935, -0.3957, -0.0753],
    [0.3198, -0.146, -0.0496],
    [0.2613, -0.1284, -0.2943],
    [-0.0547, -0.4226, -0.147],
    [-0.2368, -0.2094, -0.1659],
    [-0.1168, -0.1026, -0.3603],
]

render_pose(
    pose=pose,
    joint_links=joint_links,
    gt_pose=gt_pose,
    gt_joint_links=joint_links,
)
```
<img src="output/pose_comparison.png">

As mentioned the [human pose](./human_pose.py) script could be seen as a starter module. Referring to [other_examples](./other_examples/) and [utilities](./utils/) one could extent the module as per need. Example - adding a background wall referring to the floor object or tweaking to customize joint connection (currently not exposed) etc. Setting `gui` to true in `render_pose` will result in showing all the objects in blender. One could tweak and render in blender to find the best parameter before running the code on several inputs.

Please let me know if this is something useful by starring it. I can add more features like animation, grid of poses, adaptive camera placement etc.

## License

Same as [yuki-koyama/blender-cli-rendering](https://github.com/yuki-koyama/blender-cli-rendering)
Scripts in this repository use the Blender Python API, which is licensed under GNU General Public License (GPL). Thus, these scripts are considered as derivative works of a GPL-licensed work, so they are also licensed under GPL following the copyleft rule.