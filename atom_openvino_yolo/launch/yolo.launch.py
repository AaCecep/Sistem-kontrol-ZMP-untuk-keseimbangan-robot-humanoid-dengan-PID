#!/usr/bin/python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    ld = LaunchDescription()

    usb_cam_node = Node(
        package='usb_cam', 
        namespace='usb_cam_node',
        executable='usb_cam_node_exe', 
        output='screen',
        parameters=[{'video_device': '/dev/video0', 'image_width': 640, 'image_height': 480}],
    )

    openvino_yolo_node = Node(
        package='atom_openvino_yolo',
        namespace='atom_openvino_yolo',
        executable='openvino_yolo',
        output='screen',
        parameters=[{'confidence_threshold': 0.5}]
    )

    ld.add_action(usb_cam_node)
    ld.add_action(openvino_yolo_node)
    return ld
