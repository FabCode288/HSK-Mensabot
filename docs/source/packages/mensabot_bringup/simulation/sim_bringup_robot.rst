sim_bringup_robot.launch.py
===========================

The ``sim_bringup_robot.launch.py`` launch file starts the simulated MensaBot together with the simulated hardware interfaces.

Localization and autonomous navigation are not started, making this launch file suitable for testing and development of the simulated robot platform.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup sim_bringup_robot.launch.py

Purpose
-------

This launch file is intended for:

* Starting the simulated robot
* Testing simulated hardware interfaces
* Manual robot operation
* Simulation development and debugging

Started Components
------------------

The launch file starts the software components required for operating the simulated robot.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The simulation behavior is configured through the corresponding controller, hardware and Gazebo parameter files.