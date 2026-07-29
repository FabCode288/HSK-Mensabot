"""
Launch file for AMCL-based localization.

This launch file starts the Nav2 localization stack using Adaptive Monte
Carlo Localization (AMCL) and loads the predefined environment map together
with the project-specific localization parameters.

After the localization components have been initialized, a global
localization request is executed to distribute the initial particle set
across the entire map.

Launch Arguments:
    params_file:
        AMCL parameter file.

    map:
        Occupancy grid map used for localization.
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Create the launch description for the AMCL localization system.

    The launch description starts the Nav2 localization stack with the configured
    map and AMCL parameters. After the localization lifecycle nodes have become
    active, a global localization request is executed to initialize the particle
    filter without requiring an initial pose estimate.

    Returns:
        LaunchDescription: Launch description for the localization system.
"""

    pkg_mensabot_navigation = get_package_share_directory(
        'mensabot_navigation'
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
        'Labor16_07.yaml'
    )

    amcl_localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            nav2_localization_launch_path
        ),
        launch_arguments={
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

    return LaunchDescription([
        amcl_localization_launch,
        global_localization_call,
    ])
