real_bringup_robot.launch.py
============================

Overview
--------

The ``real_bringup_robot.launch.py`` launch file starts the hardware-related software stack of the physical MensaBot.

It initializes the robot hardware, controllers, sensors and supporting software components without starting localization or autonomous navigation.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup real_bringup_robot.launch.py

Purpose
-------

This launch file is intended for:

* Starting the physical robot
* Hardware initialization
* Manual robot operation
* Hardware testing and debugging

Started Components
------------------

The launch file starts the software components required for operating the physical robot hardware.

Launch Arguments
----------------

``lidar_reset:=true``

Performs an automatic reset of both LiDAR scanners during startup.

Example:

.. code-block:: bash

   ros2 launch mensabot_bringup real_bringup_robot.launch.py lidar_reset:=true

Related Configuration
---------------------

The hardware configuration is defined by the corresponding controller, hardware and sensor parameter files.