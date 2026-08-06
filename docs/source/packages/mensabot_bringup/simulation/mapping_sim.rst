mapping_sim.launch.py
=====================

The ``mapping_sim.launch.py`` launch file starts the mapping stack for the simulated MensaBot using SLAM Toolbox.

It is intended for creating occupancy grid maps inside the Gazebo simulation.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup mapping_sim.launch.py

Purpose
-------

This launch file is intended for:

* Creating new maps
* Recording occupancy grid maps
* Testing the mapping pipeline
* Preparing maps for autonomous navigation

Started Components
------------------

The launch file starts the software components required for mapping in the simulation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The mapping behavior is configured through the corresponding SLAM Toolbox parameter files.