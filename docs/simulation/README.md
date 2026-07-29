# Simulation

The **HSK-Mensabot** simulation provides a realistic development environment for implementing and testing the complete software stack without requiring access to the physical robot. It enables reproducible testing, simplifies software integration and allows new features to be validated before deployment on the real hardware.

The simulation has been designed to closely resemble the real robot. As a result, the transition from simulation to the physical platform only requires replacing the simulated hardware interfaces with the real sensors and actuators, while the remaining software architecture remains unchanged.
---

# 1. Simulation Architecture

The simulation is based on **Gazebo Harmonic**, which simulates the physical behavior of the robot and its environment. Visualization of the robot model, sensor data and navigation information is performed using **RViz**, while ROS2 provides the communication layer between all software components.

The figure below shows the HSK-Mensabot inside the Gazebo simulation environment.

<p align="center">
  <img src="../images/gazebo_robot.png" width="700">
</p>

A key design objective was to use the same software architecture for both simulation and real-world operation. Therefore, both operating modes share the same configuration files for robot control, localization and navigation. This ensures that parameter changes only need to be made once and remain consistent across both environments.

---

# 2. Simulated Components

The simulation reproduces all major hardware components required for autonomous navigation.

| Component | Simulation |
|-----------|------------|
| Robot Model | URDF/Xacro model |
| Differential Drive | `ros2_control` |
| LiDAR Sensors | Gazebo sensor plugins |
| IMU | Gazebo sensor plugin |
| TF System | ROS2 |
| Navigation | Nav2 |

The robot model has been simplified for the physics simulation by using simplified collision geometries and inertia properties while preserving the relevant kinematic characteristics of the real platform. This reduces computational effort without significantly affecting the simulated driving behavior.

---

# 3. Dummy Hardware

Some hardware-specific information available on the real robot cannot be generated directly by Gazebo, such as the motor connection status or the safety scanner outputs.

To provide these signals, a dedicated ROS2 node publishes simulated hardware messages on the same topics used by the real robot. As a result, higher-level software components, including the Safety Control Node, operate identically in both simulation and real-world operation without requiring separate software implementations.

[Simulation publisher node](../../src/mensabot_utils/mensabot_utils/simulation_publisher_node.py)

# 4. Sensor Simulation

The simulation includes virtual LiDAR sensors and an IMU to reproduce the sensing capabilities of the real robot.

The two simulated LiDAR sensors generate front and rear laser scans that are merged into a single scan exactly as on the physical robot. Simulated measurement noise is added to create more realistic sensor data for localization and navigation. The simulated IMU provides acceleration and angular velocity measurements, which are fused with the robot odometry by the Extended Kalman Filter (EKF). 
Communication between Gazebo and ROS2 is handled by the **ros_gz_bridge**, allowing the simulated sensors to publish the same ROS2 topics as the physical hardware. This enables localization, mapping and navigation to operate without modification in either operating mode.
---

# 5. Launch

The simulation uses dedicated launch files for starting the complete simulation environment.

Further information about the available launch files and their purpose can be found in the **[Launch Documentation](../launch/)**.

---

# Related Documentation

- **[Launch](../launch/)**
- **[Navigation](../navigation/)**
- **[Hardware](../hardware/)**
- **[Architecture](../architecture/)**