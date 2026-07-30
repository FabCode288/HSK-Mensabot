navigation_sim.launch.py
========================

The ``navigation_sim.launch.py`` launch file starts the autonomous navigation stack for the simulated MensaBot using an existing occupancy grid map.

It is intended for autonomous navigation after the robot has been successfully localized.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_sim.launch.py

Purpose
-------

This launch file is intended for:

* Autonomous navigation
* Path planning
* Path execution
* Navigation testing

Started Components
------------------

The launch file starts the software components required for autonomous navigation in the simulation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The navigation behavior is configured through the corresponding Navigation2 parameter files.