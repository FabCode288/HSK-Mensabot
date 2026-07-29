"""
Launch file for RViz visualization.

This launch file starts RViz using a configurable visualization
configuration file. RViz startup can be enabled or disabled through
a launch argument, allowing the file to be reused in automated launch
sequences where visualization is optional.

Launch Arguments:
    rviz (bool):
        Enables or disables RViz startup.

    rviz_config (str):
        Name of the RViz configuration file located in the navigation
        package.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Create the launch description for RViz.

    This launch file declares the required launch arguments and starts an
    RViz instance with the selected configuration file if visualization is
    enabled.

    Returns:
        LaunchDescription: Launch description for the RViz visualization.
    """

    pkg_mensabot_navigation = get_package_share_directory(
        'mensabot_navigation'
    )

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
        output='screen'
    )

    return LaunchDescription([
        rviz_launch_arg,
        rviz_config_arg,
        rviz_node,
    ])
