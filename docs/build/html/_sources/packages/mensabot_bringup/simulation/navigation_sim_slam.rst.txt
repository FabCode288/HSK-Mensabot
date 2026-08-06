navigation_sim_slam.launch.py
=============================

The ``navigation_sim_slam.launch.py`` launch file starts autonomous navigation while simultaneously creating a map using SLAM Toolbox.

It combines mapping and navigation within a single simulation session.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_sim_slam.launch.py

Purpose
-------

This launch file is intended for:

* Simultaneous mapping and navigation
* SLAM testing
* Navigation development
* Validation of the complete navigation pipeline

Started Components
------------------

The launch file starts the software components required for simultaneous mapping and autonomous navigation.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The behavior is configured through the corresponding SLAM Toolbox and Navigation2 parameter files.