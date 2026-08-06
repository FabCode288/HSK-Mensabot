mapping_real.launch.py
======================

Overview
--------

The ``mapping_real.launch.py`` launch file starts the mapping stack for the physical MensaBot using SLAM Toolbox.

It is intended for creating a new occupancy grid map of an unknown environment that can later be used for localization and autonomous navigation.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup mapping_real.launch.py

Purpose
-------

This launch file is intended for:

* Creating new maps of the environment
* Recording occupancy grid maps
* Testing and validating the mapping pipeline
* Preparing maps for later localization and navigation

Started Components
------------------

The launch file starts the software components required for mapping on the physical robot.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The mapping behavior is configured through the corresponding SLAM Toolbox parameter files.