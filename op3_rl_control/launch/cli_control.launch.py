from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='op3_rl_control',
            executable='cli_control_node',
            name='cli_control_node',
            output='screen',
        )
    ])
