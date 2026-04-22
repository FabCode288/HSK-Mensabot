import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.conditions import IfCondition
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    pkg_mensabot_description = get_package_share_directory('mensabot_description')
    pkg_mensabot_bringup = get_package_share_directory('mensabot_bringup')
    pkg_mensabot_simulation = get_package_share_directory('mensabot_simulation')
    pkg_mensabot_navigation = get_package_share_directory('mensabot_navigation')    
    pkg_laser_scan_merger = get_package_share_directory('laser_scan_merger')

    # Define the path to your URDF or Xacro file
    urdf_file_path = PathJoinSubstitution([
        pkg_mensabot_description,  # Replace with your package name
        "urdf",
        LaunchConfiguration('model')  # Replace with your URDF or Xacro file
    ])

    model_arg = DeclareLaunchArgument(
        'model',
        default_value='mensabot.urdf.xacro',
    )

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='True',
        description='Flag to enable use_sim_time'
    )


    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': Command(['xacro', ' ', urdf_file_path, ' use_sim:=true']),
             'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    joint_state_broadcaster_node = Node(
        package='controller_manager',
        executable='spawner',
        name='joint_state_broadcaster_spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    diff_drive_controller_node = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'mensabot_base_controller',
            '--controller-manager', '/controller_manager'
        ],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen',
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        remappings=[('/odometry/filtered', '/odom')],   # Remap the output of the EKF to /odom instead of /odometry/filtered like default
        parameters=[
            os.path.join(pkg_mensabot_simulation, 'config', 'ekf.yaml'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
             ]
    )

    cmd_vel_transform_node = Node(
        package='mensabot_utils',
        executable='cmd_vel_transform',
        name='cmd_vel_transform_node',
        output='screen'
    )

    laser_scan_merger_node = ComposableNodeContainer(
        package="rclcpp_components",
        executable="component_container",
        name="component_manager_node",
        namespace="",
        composable_node_descriptions=[
            ComposableNode(
                package="laser_scan_merger",
                plugin="util::LaserScanMerger",
                name="laser_scan_merger_node",
                parameters=[
                    os.path.join(pkg_laser_scan_merger, 'config', 'laser_merger_param.yaml'),
                    {'use_sim_time': LaunchConfiguration('use_sim_time')},
                ]
            )
        ],
        output="screen"
    )

    ####################

        # Path to the Slam Toolbox launch file
    nav2_localization_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'localization_launch.py'
    )

    nav2_navigation_launch_path = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'navigation_launch.py'
    )

    localization_params_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'config',
        'amcl_localization.yaml'
    )

    navigation_params_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'config',
        'navigation.yaml'
    )

    map_file_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'maps',
        'map3.yaml'
    )

    # Path to the Slam Toolbox launch file
    slam_toolbox_launch_path = os.path.join(
        get_package_share_directory('slam_toolbox'),
        'launch',
        'localization_launch.py'
    )

    slam_toolbox_params_path = os.path.join(
        get_package_share_directory('mensabot_navigation'),
        'config',
        'slam_toolbox_localization.yaml'
    )

    amcl_localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_localization_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'params_file': localization_params_path,
                'map': map_file_path,
        }.items()
    )

    slam_toolbox_localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'slam_params_file': slam_toolbox_params_path,
                'map': map_file_path,
        }.items()
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_navigation_launch_path),
        launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'params_file': navigation_params_path,
        }.items()
    )


    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(model_arg)
    launchDescriptionObject.add_action(sim_time_arg)
    launchDescriptionObject.add_action(robot_state_publisher_node)
    launchDescriptionObject.add_action(joint_state_broadcaster_node)
    launchDescriptionObject.add_action(diff_drive_controller_node)
    launchDescriptionObject.add_action(ekf_node)
    launchDescriptionObject.add_action(cmd_vel_transform_node)
    #launchDescriptionObject.add_action(laser_scan_merger_node)



    #launchDescriptionObject.add_action(amcl_localization_launch)
    #launchDescriptionObject.add_action(slam_toolbox_localization_launch)
    #launchDescriptionObject.add_action(navigation_launch)

    return launchDescriptionObject