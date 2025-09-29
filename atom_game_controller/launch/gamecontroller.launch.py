from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'team_number',
            default_value='1',
            description='Team number'
        ),
        DeclareLaunchArgument(
            'player_number', 
            default_value='1',
            description='Player number'
        ),
        DeclareLaunchArgument(
            'gamecontroller_ip',
            default_value='255.255.255.255',
            description='Game controller IP address'
        ),
        
        Node(
            package='atom_game_controller',
            executable='game_controller',
            name='game_controller',
            parameters=[{
                'team_number': LaunchConfiguration('team_number'),
                'player_number': LaunchConfiguration('player_number'),
                'gamecontroller_ip': LaunchConfiguration('gamecontroller_ip'),
            }],
            output='screen'
        ),
        
    ])