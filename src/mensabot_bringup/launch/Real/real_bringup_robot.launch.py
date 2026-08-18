"""
Launch file for the Mensabot real robot.

This launch file starts all software components required for operating the
physical robot, including:

- robot_state_publisher
- ros2_control
- Hardware Interface
- EKF localization
- IMU driver and Madgwick filter
- Dual LiDAR drivers
- Laser scan merger
- RF2O laser odometry
- Safety Control Node
- LiDAR Field Selection Node

The launch file also supports an optional LiDAR reset before the remaining
system components are started.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction, ExecuteProcess, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode 
from launch.event_handlers import OnProcessStart, OnProcessExit
from ament_index_python.packages import get_package_share_directory, get_package_share_path
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    """
    Create the launch description for the real Mensabot platform.

    The launch sequence initializes all required ROS 2 nodes in a controlled
    order. Event handlers are used to synchronize dependent components and
    prevent race conditions during system startup.

    Returns:
        LaunchDescription: Complete launch configuration for the real robot.
    """    

    pkg_mensabot_description = get_package_share_directory('mensabot_description')
    pkg_mensabot_bringup = get_package_share_directory('mensabot_bringup')
    pkg_mensabot_navigation = get_package_share_directory('mensabot_navigation')    
    pkg_laser_scan_merger = get_package_share_directory('laser_scan_merger')
    pkg_mensabot_hardware = get_package_share_directory('mensabot_hardware')
    pkg_mensabot_utils = get_package_share_directory('mensabot_utils')

    package_path = get_package_share_path('imu_ros2_device')
    default_rviz_config_path = package_path / 'rviz/ybimu.rviz'
    print("config path:", default_rviz_config_path)


    model_arg = DeclareLaunchArgument(
        'model',
        default_value='mensabot.urdf.xacro',
    )

    lidar_reset_arg = DeclareLaunchArgument(
        'lidar_reset',
        default_value='false',
        description='Perform lidar reset before startup'
    )

    # Define the path to your URDF or Xacro file
    urdf_file_path = PathJoinSubstitution([
        pkg_mensabot_description,  # Replace with your package name
        "urdf",
        LaunchConfiguration('model')  # Replace with your URDF or Xacro file
    ])

    controller_manager_yaml_path = os.path.join(
        pkg_mensabot_bringup,
        'config',
        'controller.yaml'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': Command(['xacro', ' ', urdf_file_path, ' use_sim:=false']), #use_sim:= false to not include gazebo specific plugins in the URDF when running on real robot
            },
        ],
    )

    joint_state_broadcaster_node = Node(
        package='controller_manager',
        executable='spawner',
        name='joint_state_broadcaster_spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    diff_drive_controller_node = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'mensabot_base_controller',
            '--controller-manager', '/controller_manager'
        ],
        output='screen',
    )

    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[{'robot_description': Command(['xacro', ' ', urdf_file_path, ' use_sim:=false']),
            },
            controller_manager_yaml_path],
        output='screen',
    )   

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        remappings=[('/odometry/filtered', '/odom')],   # Remap the output of the EKF to /odom instead of /odometry/filtered like default
        parameters=[
            os.path.join(pkg_mensabot_bringup, 'config', 'ekf.yaml'),
        ]
    )

    cmd_vel_transform_node = Node(
        package='mensabot_utils',
        executable='cmd_vel_transform',
        name='cmd_vel_transform_node',
        output='screen'
    )

    safety_control_node = Node(
        package='mensabot_utils',
        executable='safety_control_node',
        name='safety_control_node',
        parameters=[{'simulation': False}],
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
                ]
            )
        ],
        output="screen"
    )

    imu_device_node = Node(
        package='imu_ros2_device',
        executable='ybimu_driver',
        name=   'imu_device_node',
        output='screen',
    )

    imu_filter_config = os.path.join(              
        get_package_share_directory('imu_ros2_device'),
        'config',
        'imu_filter_param.yaml'
    )

    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_node',
        output='screen',
        parameters=[imu_filter_config]
    )

    delayed_joint_state_broadcaster = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager_node,
            on_start=[
                TimerAction(
                    period=0.5,
                    actions=[joint_state_broadcaster_node]
                )
            ]
        )
    )

    delayed_diff_drive_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_node,
            on_exit=[diff_drive_controller_node]
        )
    )

    scanner_front_node=Node(
        package="sick_safetyscanners2",
        executable="sick_safetyscanners2_node",
        name="sick_safetyscanners2_node_front",
        output="screen",
        emulate_tty=True,
        remappings=[('/scan', '/lidars/front/scan'), ('/extended_scan', '/lidars/front/extended_scan'), ('/output_paths', '/lidars/front/output_paths'), ('/raw_data', '/lidars/front/raw_data')], 
        parameters=[
            {"frame_id": "scan_front_link",
                "sensor_ip": "192.168.0.11",
                "host_ip": "192.168.0.100",
                "interface_ip": "0.0.0.0",
                "host_udp_port": 6060,
                "channel": 0,
                "channel_enabled": True,
                "skip": 0,
                "angle_start": -2.4,
                "angle_end": 2.4,
                "time_offset": 0.0,
                "general_system_state": True,
                "derived_settings": True,
                "measurement_data": True,
                "intrusion_data": True,
                "application_io_data": True,
                "use_persistent_config": False,
                "min_intensities": 0.0}
        ]
    )

    scanner_rear_node=Node(
        package="sick_safetyscanners2",
        executable="sick_safetyscanners2_node",
        name="sick_safetyscanners2_node_rear",
        output="screen",
        emulate_tty=True,
        remappings=[('/scan', '/lidars/rear/scan'), ('/extended_scan', '/lidars/rear/extended_scan'), ('/output_paths', '/lidars/rear/output_paths'), ('/raw_data', '/lidars/rear/raw_data')], 
        parameters=[
            {"frame_id": "scan_rear_link",
                "sensor_ip": "192.168.0.10",
                "host_ip": "192.168.0.100",
                "interface_ip": "0.0.0.0",
                "host_udp_port": 6061,
                "channel": 0,
                "channel_enabled": True,
                "skip": 0,
                "angle_start": -2.4,
                "angle_end": 2.4,
                "time_offset": 0.0,
                "general_system_state": True,
                "derived_settings": True,
                "measurement_data": True,
                "intrusion_data": True,
                "application_io_data": True,
                "use_persistent_config": False,
                "min_intensities": 0.0}
        ]
    )

    lidar_reset = ExecuteProcess(
        cmd=['python3',
        '-u',
        '/home/student/ros2_mensabot_ws/src/mensabot_utils/mensabot_utils/lidar_reset.py'],
        output='screen'
    )

    lidar_field_selection_node = Node(
        package='mensabot_utils',
        executable='lidar_field_selection_node',
        name='lidar_field_selection_node',
        parameters=[{'simulation': False}],
        output='screen'
    )

    laser_scan_matcher_node = Node(
                package='rf2o_laser_odometry',
                executable='rf2o_laser_odometry_node',
                name='rf2o_laser_odometry',
                output='screen',
                parameters=[{
                    'laser_scan_topic' : '/merged_scan',
                    'odom_topic' : '/odom_rf2o',
                    'publish_tf' : False,
                    'base_frame_id' : 'base_link',
                    'odom_frame_id' : 'odom',
                    'init_pose_from_topic' : '',
                    'freq' : 15.0}],
    )

    delayed_safety_control_node = RegisterEventHandler(
        OnProcessStart(
            target_action=lidar_field_selection_node,
            on_start=[
                TimerAction(
                    period=1.0,
                    actions=[safety_control_node]
                )
            ]
        )
    )

    normal_startup = GroupAction(
        actions=[
            controller_manager_node,
            robot_state_publisher_node,
            delayed_joint_state_broadcaster,
            delayed_diff_drive_controller,
            ekf_node,
            cmd_vel_transform_node,
            laser_scan_merger_node,
            imu_device_node,
            imu_filter_node,
            scanner_front_node,
            scanner_rear_node,
            lidar_field_selection_node,
            laser_scan_matcher_node,
            delayed_safety_control_node
        ]
    )

    delayed_startup_after_reset = RegisterEventHandler(
        OnProcessExit(
            target_action=lidar_reset,
            on_exit=[
                normal_startup
            ]
        )
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(model_arg)
    launchDescriptionObject.add_action(lidar_reset_arg)

    # ---------------------------------------
    # Start with reset
    # ---------------------------------------

    launchDescriptionObject.add_action(
        GroupAction(
            condition=IfCondition(
                LaunchConfiguration('lidar_reset')
            ),
            actions=[
                lidar_reset,
                delayed_startup_after_reset
            ]
        )
    )

    # ---------------------------------------
    # Start without reset
    # ---------------------------------------

    launchDescriptionObject.add_action(
        GroupAction(
            condition=UnlessCondition(
                LaunchConfiguration('lidar_reset')
            ),
            actions=[
                normal_startup
            ]
        )
    )


    return launchDescriptionObject