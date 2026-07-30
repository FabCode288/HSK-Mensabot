sim_complete_bringup.launch.py
==============================

The ``sim_complete_bringup.launch.py`` launch file starts the complete simulation environment.

It combines Gazebo, the simulated robot, localization and autonomous navigation into a single launch file.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup sim_complete_bringup.launch.py

Purpose
-------

This launch file is intended for:

* Complete simulation startup
* Autonomous navigation testing
* System validation
* End-to-end simulation

Started Components
------------------

The launch file starts all software components required for autonomous operation in the simulation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The behavior of the complete simulation is configured through the corresponding Gazebo, localization and Navigation2 parameter files.