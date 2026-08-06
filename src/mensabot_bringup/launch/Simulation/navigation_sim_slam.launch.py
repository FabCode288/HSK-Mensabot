"""
Launch file for simultaneous mapping and navigation in simulation.

This launch file starts the SLAM Toolbox and the Nav2 navigation stack
within the simulation environment. Simulation time is enabled and RViz can
optionally be launched for visualization.

The launch file is intended for scenarios where navigation is performed while
a map is being created or continuously updated.

Launch Arguments:
    rviz (bool):
        Enables or disables RViz startup.

    rviz_config (str):
        Name of the RViz configuration file.

    use_sim_time (bool):
        Enables simulation time provided by Gazebo.

    params_file:
        Navigation parameter file used to configure the Nav2 stack.

    slam_params_file:
        SLAM Toolbox parameter file used for map generation.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import SetRemap
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Create the launch description for simultaneous mapping and navigation.

    The launch description starts the SLAM Toolbox together with the Nav2
    navigation stack using simulation time. RViz can optionally be launched to
    visualize the mapping and navigation process.

    Returns:
        LaunchDescription: Launch description for the simulated mapping and
        navigation system.
    """

    pkg_mensabot_navigation = get_package_share_directory('mensabot_navigation')

    gazebo_models_path, ignore_last_dir = os.path.split(pkg_mensabot_navigation)
    os.environ["GZ_SIM_RESOURCE_PATH"] += os.pathsep + gazebo_models_path

    rviz_launch_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Open RViz'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='navigation.rviz',
        description='RViz config file'
    )

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='True',
        description='Flag to enable use_sim_time'
    )

    nav2_navigation_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'navigation_launch.py'
    )

    navigation_params_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'config',
        'navigation.yaml'
    )

    slam_toolbox_params_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'config',
        'slam_toolbox_mapping.yaml'
    )

    # Launch rviz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_mensabot_navigation, 'rviz', LaunchConfiguration('rviz_config')])],
        condition=IfCondition(LaunchConfiguration('rviz')),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    # Path to the Slam Toolbox launch file
    slam_toolbox_launch_path = os.path.join(
        get_package_share_directory('slam_toolbox'),
        'launch',
        'online_async_launch.py'
    )

    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'slam_params_file': slam_toolbox_params_path,
        }.items()
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_navigation_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'params_file': navigation_params_path,
        }.items()
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(rviz_launch_arg)
    launchDescriptionObject.add_action(rviz_config_arg)
    launchDescriptionObject.add_action(sim_time_arg)
    launchDescriptionObject.add_action(rviz_node)
    launchDescriptionObject.add_action(slam_toolbox_launch)
    launchDescriptionObject.add_action(navigation_launch)

    return launchDescriptionObject