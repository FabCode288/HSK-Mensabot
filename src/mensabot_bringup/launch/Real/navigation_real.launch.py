import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_mensabot_navigation = get_package_share_directory(
        'mensabot_navigation'
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

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            nav2_navigation_launch_path
        ),
        launch_arguments={
            'params_file': navigation_params_path,
        }.items()
    )

    return LaunchDescription([
        navigation_launch,
    ])
