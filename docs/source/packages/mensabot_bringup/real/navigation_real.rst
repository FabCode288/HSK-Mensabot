navigation_real.launch.py
=========================

Overview
--------

The ``navigation_real.launch.py`` launch file starts the autonomous navigation stack for the physical MensaBot using an existing occupancy grid map.

It is intended for autonomous navigation after the robot has been successfully localized.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_real.launch.py

Purpose
-------

This launch file is intended for:

* Autonomous navigation
* Path planning
* Path execution
* Navigation testing and validation

Started Components
------------------

The launch file starts the software components required for autonomous navigation on the physical robot.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The navigation behavior is configured through the corresponding Navigation2 parameter files.