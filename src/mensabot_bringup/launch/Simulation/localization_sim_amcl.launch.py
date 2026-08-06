"""
Launch file for AMCL-based localization in simulation.

This launch file starts the Nav2 localization stack using Adaptive Monte
Carlo Localization (AMCL) in the simulation environment. The simulation map
and project-specific localization parameters are loaded while simulation time
is enabled.

After the localization components have been initialized, a global
localization request is executed to distribute the initial particle set
across the entire map.

Launch Arguments:
    use_sim_time (bool):
        Enables simulation time provided by Gazebo.

    params_file:
        AMCL parameter file.

    map:
        Occupancy grid map used for localization.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Create the launch description for the simulated AMCL localization system.

    The launch description starts the Nav2 localization stack using simulation
    time, loads the configured map and AMCL parameters, and performs a global
    localization request after the localization lifecycle nodes have become
    active.

    Returns:
        LaunchDescription: Launch description for the simulated localization
        system.
    """

    pkg_mensabot_navigation = get_package_share_directory('mensabot_navigation')

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Flag to enable use_sim_time'
    )

    nav2_localization_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'localization_launch.py'
    )

    localization_params_path = os.path.join(
        pkg_mensabot_navigation,
        'config',
        'amcl_localization.yaml'
    )

    map_file_path = os.path.join(
        pkg_mensabot_navigation,
        'maps',
        'map_room.yaml'
    )

    amcl_localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            nav2_localization_launch_path
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': localization_params_path,
            'map': map_file_path,
        }.items()
    )

    # Wait until map_server and AMCL have been activated by the
    # localization lifecycle manager, then initialize AMCL globally.
    global_localization_call = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2',
                    'service',
                    'call',
                    '/reinitialize_global_localization',
                    'std_srvs/srv/Empty',
                    '{}'
                ],
                output='screen'
            )
        ]
    )

    launch_description = LaunchDescription()

    launch_description.add_action(sim_time_arg)
    launch_description.add_action(amcl_localization_launch)
    launch_description.add_action(global_localization_call)

    return launch_description
