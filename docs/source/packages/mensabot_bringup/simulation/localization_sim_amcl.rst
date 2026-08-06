localization_sim_amcl.launch.py
===============================

The ``localization_sim_amcl.launch.py`` launch file starts the localization stack for the simulated MensaBot using an existing occupancy grid map.

Unlike the complete bringup, this launch file starts only the components required for robot localization. It is intended for testing and validating the localization pipeline inside the simulation environment.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup localization_sim_amcl.launch.py

Purpose
-------

This launch file is intended for:

* Robot localization using an existing map
* Testing the localization pipeline
* Preparing the robot before autonomous navigation
* Development and debugging in simulation

Started Components
------------------

The launch file starts the software components required for localization in the simulation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The localization behavior is configured through the corresponding AMCL and Navigation2 parameter files.