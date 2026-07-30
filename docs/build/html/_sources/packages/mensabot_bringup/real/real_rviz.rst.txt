real_rviz.launch.py
===================

Overview
--------

The ``real_rviz.launch.py`` launch file starts RViz using the predefined visualization configuration of the MensaBot project.

It provides a ready-to-use visualization environment for monitoring and debugging the physical robot.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup real_rviz.launch.py

Purpose
-------

This launch file is intended for:

* Robot visualization
* System monitoring
* Sensor visualization
* Navigation debugging

Started Components
------------------

The launch file starts RViz together with the predefined project configuration.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The visualization is configured through the predefined RViz configuration file included in the project.