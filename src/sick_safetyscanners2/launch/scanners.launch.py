import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode 
from launch.event_handlers import OnProcessStart, OnProcessExit
from ament_index_python.packages import get_package_share_directory, get_package_share_path

#https://github.com/SICKAG/sick_safetyscanners2

def generate_launch_description():

    scanner_front_node=Node(
        package="sick_safetyscanners2",
        executable="sick_safetyscanners2_node",
        name="sick_safetyscanners2_node_front",
        output="screen",
        emulate_tty=True,
        remappings=[('/scan', '/scan_front')], 
        parameters=[
            {"frame_id": "scan_front_link",
                "sensor_ip": "192.168.0.11",
                "host_ip": "192.168.0.100",
                "interface_ip": "0.0.0.0",
                "host_udp_port": 6060,
                "channel": 0,
                "channel_enabled": True,
                "skip": 0,
                "angle_start": 0.0,
                "angle_end": 0.0,
                "time_offset": 0.0,
                "general_system_state": True,
                "derived_settings": True,
                "measurement_data": True,
                "intrusion_data": True,
                "application_io_data": True,
                "use_persistent_config": False,
                "min_intensities": 0.0}
        ]
    )

    scanner_rear_node=Node(
        package="sick_safetyscanners2",
        executable="sick_safetyscanners2_node",
        name="sick_safetyscanners2_node_rear",
        output="screen",
        emulate_tty=True,
        remappings=[('/scan', '/scan_rear')], 
        parameters=[
            {"frame_id": "scan_rear_link",
                "sensor_ip": "192.168.0.10",
                "host_ip": "192.168.0.100",
                "interface_ip": "0.0.0.0",
                "host_udp_port": 6061,
                "channel": 0,
                "channel_enabled": True,
                "skip": 0,
                "angle_start": 0.0,
                "angle_end": 0.0,
                "time_offset": 0.0,
                "general_system_state": True,
                "derived_settings": True,
                "measurement_data": True,
                "intrusion_data": True,
                "application_io_data": True,
                "use_persistent_config": False,
                "min_intensities": 0.0}
        ]
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(scanner_front_node)
    launchDescriptionObject.add_action(scanner_rear_node)

    return launchDescriptionObject