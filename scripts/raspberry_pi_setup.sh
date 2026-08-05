#!/bin/bash

# ============================================================
# HSK MensaBot - Raspberry Pi 5 Setup
#
# Installs and configures a complete ROS2 Jazzy development
# environment for the HSK MensaBot platform.
#
# The script installs:
#   - ROS2 Jazzy Desktop
#   - Development tools
#   - Navigation packages
#   - Gazebo
#   - RViz
#   - GPIO support
#   - VS Code
#   - Additional utilities
#
# Version: 1.1
# Tested on:
#   - Raspberry Pi 5
#   - Ubuntu 24.04 LTS
#   - ROS2 Jazzy Jalisco
# ============================================================

set -e

echo "============================================================"
echo "HSK MensaBot - Raspberry Pi Setup"
echo "============================================================"

echo "[1/16] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean

echo "[2/16] Installing basic system packages..."
sudo apt-get install -y \
    locales \
    curl \
    wget \
    gnupg2 \
    lsb-release \
    software-properties-common

sudo add-apt-repository universe -y

sudo curl -sSL \
https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
-o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt-get update

echo "[3/16] Configuring system locale..."
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

echo "[4/16] Enabling SSH service..."
sudo apt-get install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

echo "[5/16] Installing build tools and Python packages..."
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-argcomplete \
    python3-empy \
    python3-numpy \
    python3-yaml \
    python3-serial \
    python3-smbus2

echo "[6/16] Initializing rosdep..."
sudo rosdep init || true
rosdep update

echo "[7/16] Installing ROS2 Jazzy Desktop..."
sudo apt-get install -y ros-jazzy-desktop

echo "[8/16] Installing ROS2 robotics packages..."
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
    ros-jazzy-imu-filter-madgwick \
    ros-jazzy-sick-safetyscanners2-interfaces \
    ros-jazzy-sick-safetyscanners-base

echo "[9/16] Installing Gazebo integration..."
sudo apt-get install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control

echo "[10/16] Installing RViz plugins..."
sudo apt-get install -y \
    ros-jazzy-rviz-imu-plugin

echo "[11/16] Installing rqt GUI tools..."
sudo apt-get install -y \
    ros-jazzy-rqt \
    ros-jazzy-rqt-common-plugins

echo "[12/16] Installing teleoperation + joystick..."
sudo apt-get install -y \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-teleop-twist-joy \
    joystick \
    jstest-gtk

echo "[13/16] Installing additional tools and utilities..."
sudo apt-get install -y \
    terminator \
    htop \
    net-tools \
    mesa-utils \
    v4l-utils \
    gpiod \
    libgpiod-dev

python3 -m pip install --break-system-packages gpiod

sudo groupadd -f gpio
sudo usermod -aG gpio "$USER"

if [ -e /dev/gpiochip4 ]; then
    sudo chgrp gpio /dev/gpiochip4
    sudo chmod 660 /dev/gpiochip4
fi

echo "[14/16] Installing VS Code (clean & conflict-free)..."

sudo rm -f /etc/apt/sources.list.d/vscode.list
sudo rm -f /etc/apt/sources.list.d/vscode.sources
sudo rm -f /etc/apt/sources.list.d/*microsoft*.list

sudo rm -f /usr/share/keyrings/microsoft.gpg
sudo rm -f /usr/share/keyrings/packages.microsoft.gpg

curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
gpg --dearmor > packages.microsoft.gpg

sudo install \
    -D \
    -o root \
    -g root \
    -m 644 \
    packages.microsoft.gpg \
    /usr/share/keyrings/packages.microsoft.gpg

rm packages.microsoft.gpg

echo "deb [arch=arm64 signed-by=/usr/share/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | \
sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null

sudo apt-get update
sudo apt-get install -y code

echo "[15/16] Updating installed packages..."
sudo apt-get upgrade -y

echo "[16/16] Setting up ROS2 environment..."

grep -qxF "source /opt/ros/jazzy/setup.bash" ~/.bashrc || \
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

grep -qxF "export ROS_DOMAIN_ID=3" ~/.bashrc || \
echo "export ROS_DOMAIN_ID=3" >> ~/.bashrc

if ! grep -q "ros2_mensabot_ws/install/setup.bash" ~/.bashrc; then
cat <<'EOF' >> ~/.bashrc

if [ -f ~/ros2_mensabot_ws/install/setup.bash ]; then
    source ~/ros2_mensabot_ws/install/setup.bash
fi
EOF
fi

echo
echo "============================================================"
echo "Setup completed successfully."
echo
echo "Please restart your terminal or execute:"
echo
echo "    source ~/.bashrc"
echo
echo "A reboot is recommended if kernel or graphics packages were updated."
echo
echo "You can now clone and build the HSK MensaBot workspace."
echo "============================================================"