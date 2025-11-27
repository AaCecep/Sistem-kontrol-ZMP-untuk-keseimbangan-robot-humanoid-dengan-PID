from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    ld = LaunchDescription()
    
    # =============================
    # 1. GUI DEMO NODE
    # =============================
    op3_gui_demo_pkg_path = FindPackageShare('op3_gui_demo')
    demo_config_path = PathJoinSubstitution([op3_gui_demo_pkg_path, 'config', 'gui_config.yaml'])

    op3_gui_demo_node = Node(
        package='op3_gui_demo', 
        executable='op3_gui_demo', 
        output='screen',
        parameters=[{"demo_config": demo_config_path}],
        remappings=[('/op3_demo/ik_target_pose', '/pose_panel/pose')],
    )

    # =============================
    # 2. INCLUDE MANAGER LAUNCH
    # =============================
    manager_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('op3_manager'),
            '/launch/op3_manager.launch.py'
        ])
    )

    # Tambahkan keduanya ke LaunchDescription
    ld.add_action(manager_launch)
    ld.add_action(op3_gui_demo_node)

    return ld
