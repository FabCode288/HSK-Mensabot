import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_mensabot_bringup = get_package_share_directory(
        'mensabot_bringup'
    )

    mapping_arg = DeclareLaunchArgument(
        'mapping',
        default_value='False',
        description='Start SLAM mapping instead of localization/navigation'
    )

    sim_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch',
                'Simulation',
                'sim_bringup.launch.py'
            )
        )
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch',
                'Simulation',
                'localization_sim_amcl.launch.py'
            )
        ),
        condition=UnlessCondition(
            LaunchConfiguration('mapping')
        )
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch',
                'Simulation',
                'navigation_sim.launch.py'
            )
        ),
        condition=UnlessCondition(
            LaunchConfiguration('mapping')
        )
    )

    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_mensabot_bringup,
                'launch',
                'Simulation',
                'mapping_sim.launch.py'
            )
        ),
        condition=IfCondition(
            LaunchConfiguration('mapping')
        )
    )

    delayed_localization = TimerAction(
        period=3.0,
        actions=[
            localization_launch
        ],
        condition=UnlessCondition(
            LaunchConfiguration('mapping')
        )
    )

    delayed_navigation = TimerAction(
        period=6.0,
        actions=[
            navigation_launch
        ],
        condition=UnlessCondition(
            LaunchConfiguration('mapping')
        )
    )

    delayed_mapping = TimerAction(
        period=6.0,
        actions=[
            mapping_launch
        ],
        condition=IfCondition(
            LaunchConfiguration('mapping')
        )
    )

    return LaunchDescription([
        mapping_arg,
        sim_bringup_launch,
        delayed_localization,
        delayed_navigation,
        delayed_mapping,
    ])