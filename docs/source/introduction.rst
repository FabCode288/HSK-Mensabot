Introduction
============

MensaBot is a ROS 2-based mobile robot platform designed for autonomous indoor navigation. The project combines navigation, localization, hardware control, functional safety, and simulation within a unified software architecture.

The software supports both simulation and operation on the physical robot while maintaining a nearly identical software stack in both environments.

Features
--------

The project includes the following core components:

* Autonomous navigation using Nav2
* SLAM Toolbox for map creation
* AMCL localization
* ros2_control hardware interface
* Differential drive robot control
* Integrated safety monitoring
* Gazebo simulation environment
* Hardware abstraction for real and simulated operation

System Requirements
-------------------

The project is developed and tested with the following software versions:

================== =====================
Operating System   Ubuntu 24.04 LTS
ROS Distribution   ROS 2 Jazzy Jalisco
Simulation         Gazebo Harmonic
================== =====================

Repository Structure
--------------------

The repository is organized into multiple ROS 2 packages. Each package is responsible for a dedicated subsystem such as navigation, hardware control, simulation, or utility functions.

The following chapters describe the installation procedure, software architecture, and basic operation of the system.