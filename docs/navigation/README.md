# Navigation

The **HSK-Mensabot** uses the ROS2 Navigation Stack (**Nav2**) to perform autonomous indoor navigation. The navigation system combines localization, mapping, global path planning, local trajectory generation, and motion control into a unified software architecture. The same navigation framework is used for both simulation and the physical robot, allowing algorithms and configurations to be tested in simulation before deployment on real hardware.

---

# 1. Navigation Pipeline

The navigation system consists of several software components that continuously exchange information to estimate the robot pose, generate collision-free paths and execute autonomous motion.

<p align="center">
  <img src="../images/dataflow.png" width="900">
</p>

The overall navigation process follows these steps:

1. Environmental data is acquired by the LiDAR sensors.
2. Sensor data is merged and processed for localization.
3. The robot pose is estimated using multiple sensor sources.
4. Nav2 computes a collision-free path towards the goal.
5. Safe velocity commands are generated.
6. The Safety Control Node validates the commanded motion.
7. Commands are transmitted to the motor controller through the hardware interface.

---

# 2. Localization

Reliable localization is essential for autonomous navigation. The HSK-Mensabot combines multiple sensor sources to estimate the robot pose with increased robustness and accuracy.

The localization pipeline consists of the following components:

| Component                    | Purpose                                       |
| ---------------------------- | --------------------------------------------- |
| AMCL                         | Global localization using an existing map     |
| Extended Kalman Filter (EKF) | Sensor fusion                                 |
| RF2O Laser Odometry          | Laser-based odometry estimation               |
| Wheel Odometry               | Motion estimation from the drive system       |
| IMU                          | Orientation and angular velocity measurements |

The Extended Kalman Filter combines wheel odometry, IMU data and laser odometry into a single filtered odometry estimate. This estimate is then used together with the merged laser scans by AMCL to determine the robot pose within a previously created map.

---

# 3. Mapping

The HSK-Mensabot uses **SLAM Toolbox** for creating new maps of unknown environments.

Separate launch files are available for simulation and the physical robot.

| Launch File              | Purpose                                     |
| ------------------------ | ------------------------------------------- |
| `mapping_real.launch.py` | Creates a map using the physical robot.     |
| `mapping_sim.launch.py`  | Creates a map inside the Gazebo simulation. |

The generated maps can subsequently be used for localization and autonomous navigation.

---

# 4. Autonomous Navigation

Autonomous navigation is performed using the ROS2 Navigation Stack (**Nav2**).

After receiving a navigation goal, Nav2 computes a collision-free global path and continuously generates local motion commands while considering the current environment.

The navigation system of the HSK-Mensabot uses the following planning algorithms:

| Component        | Algorithm       |
| ---------------- | --------------- |
| Global Planner   | NavFn Planner   |
| Local Controller | MPPI Controller |

The **NavFn Planner** computes the global path from the current robot position to the desired goal, while the **MPPI (Model Predictive Path Integral) Controller** continuously generates smooth local trajectories and obstacle avoidance commands during robot motion.

Separate launch files are provided for simulation and real robot operation.

| Launch File                 | Purpose                                             |
| --------------------------- | --------------------------------------------------- |
| `navigation_real.launch.py` | Starts autonomous navigation on the physical robot. |
| `navigation_sim.launch.py`  | Starts autonomous navigation inside Gazebo.         |

---

# 5. Costmaps

The navigation stack uses two independent costmaps to represent the robot environment.

| Costmap        | Purpose                                                                                                                      |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Global Costmap | Represents the complete known environment and is used for global path planning.                                              |
| Local Costmap  | Represents obstacles in the robot's immediate surroundings and is used for local trajectory planning and obstacle avoidance. |

Both costmaps are continuously updated using the merged LiDAR data, enabling the robot to react to dynamic obstacles while maintaining a globally consistent navigation strategy.

---

# 6. Robot Footprint

The robot footprint defines the physical dimensions considered during path planning and obstacle avoidance.

Unlike a conventional static footprint, the HSK-Mensabot supports **dynamic footprint adaptation**. Depending on the currently active safety field, the footprint can be adjusted during operation to reflect the effective safety area of the robot.

This approach improves navigation in confined environments while maintaining compatibility with the active safety configuration.

---

# 7. Navigation Modes

Different operating modes are available depending on the intended application.

| Mode         | Launch File                                                            | Description                                           |
| ------------ | ---------------------------------------------------------------------- | ----------------------------------------------------- |
| Mapping      | `mapping_real.launch.py` / `mapping_sim.launch.py`                     | Creates a new map using SLAM Toolbox.                 |
| Localization | `localization_real_amcl.launch.py` / `localization_sim_amcl.launch.py` | Localizes the robot within an existing map.           |
| Navigation   | `navigation_real.launch.py` / `navigation_sim.launch.py`               | Performs autonomous navigation using an existing map. |

---

# 8. Configuration Files

The navigation system is configured using several YAML configuration files.

| Configuration File       | Purpose                                                                 |
| ------------------------ | ----------------------------------------------------------------------- |
| `navigation.yaml`        | Navigation2 configuration including planners, controllers and costmaps. |
| `amcl_localization.yaml` | AMCL localization parameters.                                           |
| `ekf.yaml`               | Extended Kalman Filter configuration. (In mensabot_bringup)             |

These files define the behavior of the navigation stack and allow the system to be adapted to different robot platforms without modifying the application code.

---

# 9. HSK-Mensabot Specific Features

The HSK-Mensabot extends the standard Nav2 framework with several project-specific features.

* Dual SICK NanoScan3 safety scanners with merged laser scans.
* Sensor fusion using wheel odometry, IMU data and RF2O laser odometry.
* Dynamic robot footprint adaptation based on the active safety configuration.
* Dedicated Safety Control Node positioned between navigation and hardware control.
* Unified navigation architecture for simulation and the physical robot.

These extensions improve robustness, simplify testing and ensure consistent behavior across both operating environments.

---

# Related Documentation

Further information can be found in the following documentation.

* **[Software Architecture](../architecture/)**
* **[Launch Documentation](../launch/)**
* **[Safety Documentation](../safety/)**
* **[Hardware Documentation](../hardware/)**
* **[Communication Documentation](../communication/)**

These documents describe the individual software components, hardware interfaces and safety mechanisms that complement the navigation system.
