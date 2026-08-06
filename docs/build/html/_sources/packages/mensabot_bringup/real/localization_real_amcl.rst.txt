localization_real_amcl.launch.py
================================

Overview
--------

The ``localization_real_amcl.launch.py`` launch file starts the localization stack for the physical MensaBot using an existing occupancy grid map.

Unlike the complete bringup, this launch file starts only the components required for robot localization. It is intended for scenarios where the robot position shall be estimated without starting autonomous navigation.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup localization_real_amcl.launch.py

Purpose
-------

This launch file is intended for:

* Robot localization using an existing map
* Testing and validating the localization pipeline
* Preparing the robot before autonomous navigation
* Development and debugging of the localization system

Started Components
------------------

The launch file starts the software components required for localization on the physical robot.

The detailed list of launched nodes and included launch files is defined inside the launch file implementation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The localization behavior is configured through the corresponding AMCL and Navigation2 parameter files.
