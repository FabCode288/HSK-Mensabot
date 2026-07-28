# Installation Guide

This guide describes how to install and configure the **HSK MensaBot** software on a new system. It covers the basic workspace setup, Raspberry Pi configuration, USB device mapping, and verification steps required to run the project.

---

# 1. System Requirements

## Operating System

* Ubuntu 24.04 LTS

## ROS Distribution

* ROS2 Jazzy Jalisco

## Supported Platforms

| Feature                   | Desktop PC | Raspberry Pi 5 |
| :------------------------ | :--------: | :------------: |
| Workspace Build           |      ✓     |        ✓       |
| Gazebo Simulation         |      ✓     |        ✓       |
| Real Robot Operation      |      ✗     |        ✓       |
| Raspberry Pi Setup Script |      ✗     |        ✓       |

> **Note:**
> The Raspberry Pi setup script is specifically designed and tested for a Raspberry Pi 5 running Ubuntu 24.04 LTS. Its use on other hardware platforms is not supported.

---

# 2. Workspace Setup

Create a new ROS2 workspace and clone the repository:

```bash
mkdir -p ~/ros2_mensabot_ws/src
cd ~/ros2_mensabot_ws/src

git clone https://github.com/FabCode288/HSK-Mensabot.git

cd ..

colcon build --symlink-install

source install/setup.bash
```

---

# 3. Raspberry Pi Setup (Optional)

For operation on the real robot, an automated setup script is provided.

The script installs and configures:

* ROS2 Jazzy Desktop
* Build tools
* ROS2 dependencies
* Navigation2
* SLAM Toolbox
* ros2_control
* Gazebo
* RViz
* GPIO support
* VS Code
* ROS environment variables

Run the setup script:

```bash
cd scripts

chmod +x raspberry_pi_setup.sh

./raspberry_pi_setup.sh
```

The script is available in:

```text
scripts/raspberry_pi_setup.sh
```

For a detailed description of the setup process, see the **[Raspberry Pi Setup Guide](raspberry_pi_setup.md)**.

---

# 4. USB Configuration (Real Robot Only)

The real robot uses persistent USB device names generated through **udev rules**. This prevents changing Linux device names after rebooting or reconnecting USB devices.

## Current USB Port Assignment

| Raspberry Pi USB Port | Assigned Device          |
| --------------------- | ------------------------ |
| Upper Left            | Available                |
| Upper Right           | Available                |
| Lower Left            | IMU                      |
| Lower Right           | Arduino Motor Controller |

> **Important:**
> The current udev configuration assumes that all devices remain connected to these USB ports. Moving a device to another port requires updating the corresponding udev rule.

A detailed explanation of the USB mapping procedure is available in the **[USB Configuration Guide](usb_configuration.md)**.

---

# 5. Verify the Installation

After building the workspace, verify that ROS2 can detect the installed packages.

```bash
ros2 pkg list
```

Optionally, verify the installation by launching either the simulation or the real robot.

Simulation:

```bash
ros2 launch mensabot_bringup sim_bringup.launch.py
```

Real Robot:

```bash
ros2 launch mensabot_bringup real_bringup.launch.py
```

---

# 6. Troubleshooting

## Workspace build fails

* Verify that ROS2 Jazzy is installed correctly.
* Ensure all dependencies have been installed.
* Delete the `build`, `install`, and `log` directories before rebuilding.

## Arduino not detected

* Verify the USB connection.
* Check whether `/dev/arduino` exists.
* Verify the configured udev rule.

## IMU not detected

* Verify the USB connection.
* Check whether `/dev/myimu` exists.
* Verify the configured udev rule.

## Missing ROS Packages

If packages cannot be found, verify that the workspace has been sourced:

```bash
source install/setup.bash
```

---

# Related Documentation

* **[Raspberry Pi Setup Guide](raspberry_pi_setup.md)**
* **[USB Configuration Guide](usb_configuration.md)**
* **[Launch Documentation](../launch/README.md)**
* **[Hardware Documentation](../hardware/README.md)**

