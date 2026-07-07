import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_mensabot_bringup = get_package_share_directory(
        'mensabot_bringup'
    )

    real_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch/Real',
                'real_bringup.launch.py'
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
