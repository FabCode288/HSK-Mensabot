"""
Launch file for the complete Mensabot software stack.

This launch file starts the complete software system for the physical robot by
including the individual launch files for robot bringup, localization and
navigation.

Startup delays are used to ensure that hardware, localization and navigation
components are initialized in the required order.

Included launch files:
    - real_bringup.launch.py
    - localization_real_amcl.launch.py
    - navigation_real.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Create the launch description for the complete real robot system.

    The launch process is divided into multiple stages. First, the robot hardware
    and core system components are started. Localization is launched after a short
    delay, followed by the navigation stack once the localization system has been
    initialized.

    Returns:
        LaunchDescription: Complete launch description for the real robot.
    """

    pkg_mensabot_bringup = get_package_share_directory(
        'mensabot_bringup'
    )

    real_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Real',
                'real_bringup_robot.launch.py'
            )
        )
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Real',
                'localization_real_amcl.launch.py'
            )
        )
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Real',
                'navigation_real.launch.py'
            )
        )
    )

    delayed_localization = TimerAction(
        period=5.0,
        actions=[
            localization_launch
        ]
    )

    delayed_navigation = TimerAction(
        period=12.0,
        actions=[
            navigation_launch
        ]
    )

    return LaunchDescription([
        real_bringup_launch,
        delayed_localization,
        delayed_navigation,
    ])
