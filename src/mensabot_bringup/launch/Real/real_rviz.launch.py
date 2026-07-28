from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

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
