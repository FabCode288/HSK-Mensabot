import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

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
        'labor2.yaml'
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
