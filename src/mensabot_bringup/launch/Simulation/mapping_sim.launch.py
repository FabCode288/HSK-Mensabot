"""
Launch file for SLAM-based map creation in simulation.

This launch file starts the SLAM Toolbox in asynchronous online mapping mode
within the simulation environment. Simulation time is enabled and RViz can be
optionally launched for real-time visualization of the mapping process.

Launch Arguments:
    rviz (bool):
        Enables or disables RViz startup.

    rviz_config (str):
        Name of the RViz configuration file used for mapping.

    use_sim_time (bool):
        Enables simulation time provided by Gazebo.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Create the launch description for the simulated mapping system.

    The launch description starts the SLAM Toolbox using simulation time and the
    project-specific mapping configuration. RViz can optionally be launched to
    visualize the generated occupancy grid map during the mapping process.

    Returns:
        LaunchDescription: Launch description for the simulated mapping system.
    """

    pkg_mensabot_simulation = get_package_share_directory('mensabot_simulation')

    rviz_launch_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Open RViz'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='mapping.rviz',
        description='RViz config file'
    )

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='True',
        description='Flag to enable use_sim_time'
    )

    # Path to the Slam Toolbox launch file
    slam_toolbox_launch_path = os.path.join(
        get_package_share_directory('slam_toolbox'),
        'launch',
        'online_async_launch.py'
    )

    slam_toolbox_params_path = os.path.join(
        get_package_share_directory('mensabot_simulation'),
        'config',
        'slam_toolbox_mapping.yaml'
    )

    # Launch rviz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_mensabot_simulation, 'rviz', LaunchConfiguration('rviz_config')])],
        condition=IfCondition(LaunchConfiguration('rviz')),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'slam_params_file': slam_toolbox_params_path,
        }.items()
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(rviz_launch_arg)
    launchDescriptionObject.add_action(rviz_config_arg)
    launchDescriptionObject.add_action(sim_time_arg)
    launchDescriptionObject.add_action(rviz_node)
    launchDescriptionObject.add_action(slam_toolbox_launch)

    return launchDescriptionObject
