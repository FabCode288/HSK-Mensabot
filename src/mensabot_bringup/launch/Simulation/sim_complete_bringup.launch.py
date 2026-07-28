import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_mensabot_bringup = get_package_share_directory(
        'mensabot_bringup'
    )

    sim_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Simulation',
                'sim_bringup_robot.launch.py'
            )
        )
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Simulation',
                'localization_sim_amcl.launch.py'
            )
        )
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Simulation',
                'navigation_sim.launch.py'
            )
        )
    )

    delayed_localization = TimerAction(
        period=3.0,
        actions=[
            localization_launch
        ]
    )

    delayed_navigation = TimerAction(
        period=6.0,
        actions=[
            navigation_launch
        ]
    )

    return LaunchDescription([
        sim_bringup_launch,
        delayed_localization,
        delayed_navigation,
    ])