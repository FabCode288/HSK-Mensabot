# Third-Party Software

The HSK MensaBot project is built upon several excellent open-source projects from the ROS community. This document provides an overview of the external software used within this repository.

---

| Project | Used For | Repository | License |
|---------|----------|------------|---------|
| Navigation2 (Nav2) | Autonomous navigation | https://github.com/ros-navigation/navigation2 | Apache 2.0 |
| SLAM Toolbox | Mapping and localization | https://github.com/SteveMacenski/slam_toolbox | LGPL-2.1 |
| robot_localization | EKF sensor fusion | https://github.com/cra-ros-pkg/robot_localization | BSD 3-Clause |
| RF2O Laser Odometry | Laser odometry | https://github.com/MAPIRlab/rf2o_laser_odometry | BSD 3-Clause |
| laser_scan_merger | Merge multiple LiDAR scans | https://github.com/BruceChanJianLe/laser_scan_merger | Apache 2.0 |
| SICK Safety Scanners ROS2 Driver | NanoScan3 ROS2 driver | https://github.com/SICKAG/sick_safetyscanners2 | Apache 2.0 |
| SICK Safety Scanners Base | Scanner communication library | https://github.com/SICKAG/sick_safetyscanners_base | Apache 2.0 |
| imu_ros2 | IMU driver | https://github.com/NEU-REAL/imu_ros2 | Apache 2.0 |

---

## Navigation2 (Nav2)

**Purpose**

Provides autonomous navigation including global planning, local planning, behavior trees, recovery behaviors, and localization integration.

**Repository**

https://github.com/ros-navigation/navigation2

**Documentation**

https://navigation.ros.org

**License**

Apache License 2.0

---

## SLAM Toolbox

**Purpose**

Used for 2D simultaneous localization and mapping (SLAM), map creation, and map serialization.

**Repository**

https://github.com/SteveMacenski/slam_toolbox

**License**

LGPL-2.1

---

## robot_localization

**Purpose**

Sensor fusion using an Extended Kalman Filter (EKF) for wheel odometry, IMU and laser odometry.

**Repository**

https://github.com/cra-ros-pkg/robot_localization

**Documentation**

http://wiki.ros.org/robot_localization

**License**

BSD 3-Clause License

---

## RF2O Laser Odometry

**Purpose**

Provides laser-based odometry estimation used as an additional input for the Extended Kalman Filter.

**Repository**

https://github.com/MAPIRlab/rf2o_laser_odometry

**License**

BSD 3-Clause License

---

## Laser Scan Merger

**Purpose**

Merges multiple LiDAR scans into a single LaserScan message for navigation and localization.

**Repository**

https://github.com/BruceChanJianLe/laser_scan_merger

**License**

Apache License 2.0

---

## SICK Safety Scanners ROS2 Driver

**Purpose**

ROS2 driver for the SICK NanoScan3 safety laser scanners.

**Repository**

https://github.com/SICKAG/sick_safetyscanners2

**License**

Apache License 2.0

---

## SICK Safety Scanners Base Library

**Purpose**

Low-level communication library for SICK safety scanners.

**Repository**

https://github.com/SICKAG/sick_safetyscanners_base

**License**

Apache License 2.0

---

## IMU ROS2 Device

**Purpose**

ROS2 driver providing IMU measurements used by the localization system.

**Repository**

https://github.com/NEU-REAL/imu_ros2

**License**

Apache License 2.0

---

# Notes

This repository contains custom software developed specifically for the HSK MensaBot project. All third-party software remains subject to the respective licenses provided by their original authors.

Please refer to the individual repositories for detailed licensing information and attribution requirements.
