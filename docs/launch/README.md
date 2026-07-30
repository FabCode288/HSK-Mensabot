# Launch Files

The **HSK-Mensabot** project provides a collection of launch files for both simulation and real robot operation. To simplify development and maintenance, the launch files are separated into dedicated directories for the physical robot and the Gazebo simulation while following the same software architecture whenever possible.

Depending on the desired operating mode, individual launch files can be used to start hardware components, localization, mapping, navigation, or the complete software stack.

---

# 1. Launch Directory Structure

The launch files are located in the `mensabot_bringup` package and are separated into two groups.

```text
launch/

├── Real/
│   ├── real_bringup_robot.launch.py
│   ├── real_complete_bringup.launch.py
│   ├── localization_real_amcl.launch.py
│   ├── navigation_real.launch.py
│   ├── mapping_real.launch.py
│   └── real_rviz.launch.py
│
└── Simulation/
    ├── sim_bringup_robot.launch.py
    ├── sim_complete_bringup.launch.py
    ├── localization_sim_amcl.launch.py
    ├── navigation_sim.launch.py
    ├── navigation_sim_slam.launch.py
    └── mapping_sim.launch.py
```

The separation between **Real** and **Simulation** allows both operating modes to use nearly identical software while replacing only the hardware-dependent components.

---

# 2. Operating Modes

The launch files are organized into different operating modes depending on the desired application.

| Mode                 | Description                                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Bringup Robot**          | Starts the robot hardware or simulated robot without localization or navigation. Intended for testing, debugging and manual operation. |
| **Localization**     | Starts AMCL localization using an existing map without autonomous navigation.                                                          |
| **Navigation**       | Starts autonomous navigation using a previously created map.                                                                           |
| **Mapping**          | Starts SLAM Toolbox to create a new map of the environment.                                                                            |
| **Complete Bringup** | Starts the complete software stack required for autonomous robot operation.                                                            |

---

# 3. Available Launch Files

## 3.1 Real Robot

The following launch files are available for operating the physical HSK-Mensabot.

| Launch File                        | Description                                                                                                                                           |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `real_bringup_robot.launch.py`           | Starts the hardware interface, controllers, sensors, safety system and all required hardware components. Navigation and localization are not started. |
| `real_complete_bringup.launch.py`          | Starts the complete robot including hardware, localization and autonomous navigation.                                                                 |
| `mapping_real.launch.py`           | Starts SLAM Toolbox for creating a new map of the environment.                                                                                        |
| `navigation_real.launch.py`        | Starts autonomous navigation using an existing map.                                                                                                   |
| `localization_real_amcl.launch.py` | Starts AMCL localization using a previously generated map.                                                                                            |
| `real_rviz.launch.py`              | Starts RViz using the predefined project visualization configuration on the computer of the user.                                                                                 |

---

## 3.2 Simulation

The following launch files are available for the Gazebo simulation.

| Launch File                       | Description                                                                                                              |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `sim_bringup_robot.launch.py`     | Starts the simulated robot together with the simulated hardware interfaces. Localization and navigation are not started. |
| `sim_complete_bringup.launch.py`  | Starts the complete simulation including Gazebo, localization and autonomous navigation.                                 |
| `mapping_sim.launch.py`           | Starts SLAM Toolbox to create a new map inside the simulation.                                                           |
| `navigation_sim.launch.py`        | Starts autonomous navigation using an existing map.                                                                      |
| `navigation_sim_slam.launch.py`   | Starts autonomous navigation while simultaneously creating a map using SLAM Toolbox.                                     |
| `localization_sim_amcl.launch.py` | Starts AMCL localization using an existing map inside the simulation.                                                    |

---

# 4. Launch Arguments

Some launch files provide optional launch arguments for additional functionality.

| Launch File              | Argument            | Description                                                        |
| ------------------------ | ------------------- | ------------------------------------------------------------------ |
| `real_bringup_robot.launch.py` | `lidar_reset:=true` | Performs an automatic reset of both LiDAR scanners during startup. |

> **Note**
> The `lidar_reset` launch argument is only available for `real_bringup_robot.launch.py`. It is **not** supported by `real_complete_bringup.launch.py`.

Example:

```bash
ros2 launch mensabot_bringup real_bringup_robot.launch.py lidar_reset:=true
```

---

# 5. Related Documentation

Further information about individual software components can be found in the following documentation.

* **[Installation Guide](../installation/)**
* **[Software Architecture](../architecture/)**
* **[Navigation Documentation](../navigation/)**
* **[Safety Documentation](../safety/)**
* **[Hardware Documentation](../hardware/)**

These documents provide detailed information about the implementation, configuration and interaction of the individual software components.
