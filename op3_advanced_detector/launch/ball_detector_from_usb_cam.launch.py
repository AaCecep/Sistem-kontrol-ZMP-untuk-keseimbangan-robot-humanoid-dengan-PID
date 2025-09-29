import launch
import launch_ros.actions
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get share directory if perlu, misal untuk config, model dll
    op3_share_dir = get_package_share_directory('op3_advanced_detector')

    webcam = launch_ros.actions.Node(
        package='usb_cam', 
        executable='usb_cam_node_exe',
        name="webcam",
        parameters=[
            {"image_size": [640, 480]},
        ],
        output="screen"
    )

    op3_detector_node = launch_ros.actions.Node(
        package="op3_advanced_detector",
        executable="op3_advanced_detector",  # Pastikan nama executable sesuai
        name="op3_advanced_detector_node",
        parameters=[
            # Tambahkan parameter jika perlu, misal:
            # {"view_img": True},
        ],
        output="screen"
    )

    return launch.LaunchDescription([
        webcam,
        op3_detector_node,
    ])
