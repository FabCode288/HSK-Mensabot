#!/bin/bash

# ============================================================
# ROS2 Jazzy Desktop Setup für Raspberry Pi 5
# Vollsetup für mobilen Roboter (Nav2, Gazebo, RViz, Teleop)
# ============================================================

set -e

echo ">>> 1. Systemupdate und Upgrade"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean

echo ">>> 2. Grundlegende Pakete installieren"
sudo apt-get install -y \
locales curl gnupg2 lsb-release software-properties-common

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
-o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt-get update

echo ">>> 3. Locale setzen"
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

echo ">>> 4. SSH aktivieren"
sudo systemctl enable ssh
sudo systemctl start ssh

echo ">>> 5. Build-Tools und Python"
sudo apt-get install -y \
build-essential cmake git python3-pip \
python3-rosdep python3-colcon-common-extensions \
python3-vcstool python3-argcomplete \
python3-empy python3-numpy python3-yaml \
python3-serial python3-smbus2

echo ">>> 6. rosdep initialisieren"
sudo rosdep init || true
rosdep update

echo ">>> 7. ROS2 Jazzy Desktop installieren"
sudo apt-get install -y ros-jazzy-desktop

echo ">>> 8. ROS2 Robotik Pakete"
sudo apt-get install -y \
ros-jazzy-ros2-control \
ros-jazzy-ros2-controllers \
ros-jazzy-joint-state-broadcaster \
ros-jazzy-robot-state-publisher \
ros-jazzy-xacro \
ros-jazzy-cv-bridge \
ros-jazzy-nav2-bringup \
ros-jazzy-navigation2 \
ros-jazzy-slam-toolbox \
ros-jazzy-imu-filter-madgwick

echo ">>> 9. Gazebo Sim + ROS Integration"
sudo apt-get install -y \
ros-jazzy-ros-gz \
ros-jazzy-gz-ros2-control

echo ">>> 10. RViz Plugins"
sudo apt-get install -y \
ros-jazzy-rviz-imu-plugin

echo ">>> 11. rqt GUI Tools"
sudo apt-get install -y \
ros-jazzy-rqt \
ros-jazzy-rqt-common-plugins

echo ">>> 12. Teleoperation + Joystick"
sudo apt-get install -y \
ros-jazzy-teleop-twist-keyboard \
ros-jazzy-teleop-twist-joy \
joystick \
jstest-gtk

echo ">>> 13. Zusätzliche Tools"
sudo apt-get install -y \
terminator \
htop \
net-tools \
mesa-utils \
v4l-utils

echo ">>> 14. System final updaten (ROS Updates)"
sudo apt-get update
sudo apt-get upgrade -y

echo ">>> 15. ROS2 Environment setzen"
if ! grep -Fxq "source /opt/ros/jazzy/setup.bash" ~/.bashrc; then
  echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
fi

if ! grep -Fxq "export ROS_DOMAIN_ID=3" ~/.bashrc; then
  echo "export ROS_DOMAIN_ID=3" >> ~/.bashrc
fi

echo ">>> 16. Installation abgeschlossen"
echo ""