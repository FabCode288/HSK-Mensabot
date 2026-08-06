"""
Launch file for the Nav2 navigation stack in simulation.

This launch file starts the ROS 2 Navigation (Nav2) stack in the simulation
environment using the project-specific navigation configuration. Simulation
time is enabled and RViz can optionally be launched for visualization.

Launch Arguments:
    rviz (bool):
        Enables or disables RViz startup.

    rviz_config (str):
        Name of the RViz configuration file.

    use_sim_time (bool):
        Enables simulation time provided by Gazebo.

    params_file:
        Navigation parameter file used to configure the Nav2 stack.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    """
    Create the launch description for the simulated Nav2 navigation stack.

    The launch description starts the Nav2 navigation stack using simulation
    time and the project-specific navigation configuration. RViz can optionally
    be launched for visualizing the navigation process.

    Returns:
        LaunchDescription: Launch description for the simulated navigation
        system.
    """

    pkg_mensabot_navigation = get_package_share_directory('mensabot_navigation')

    rviz_launch_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Open RViz'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value='navigation.rviz',
        description='RViz config file'
    )

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Flag to enable use_sim_time'
    )

    nav2_navigation_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'navigation_launch.py'
    )

    navigation_params_path = os.path.join(
        pkg_mensabot_navigation,
        'config',
        'navigation.yaml'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=[
            '-d',
            PathJoinSubstitution([
                pkg_mensabot_navigation,
                'rviz',
                LaunchConfiguration('rviz_config')
            ])
        ],
        condition=IfCondition(
            LaunchConfiguration('rviz')
        ),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            nav2_navigation_launch_path
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': navigation_params_path,
        }.items()
    )

    launch_description = LaunchDescription()

    launch_description.add_action(rviz_launch_arg)
    launch_description.add_action(rviz_config_arg)
    launch_description.add_action(sim_time_arg)
    launch_description.add_action(rviz_node)
    launch_description.add_action(navigation_launch)

    return launch_description
