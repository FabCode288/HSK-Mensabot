Navigation
==========

The ``mensabot_navigation`` package contains all configuration files required for the ROS 2 navigation stack of the MensaBot.

These parameter files define the behavior of localization, mapping and autonomous navigation for both the physical robot and the Gazebo simulation. They allow the navigation system to be adapted without modifying the application source code.

Available Configuration Files
-----------------------------

+-----------------------------------+--------------------------------------------------------------+
| File                              | Description                                                  |
+===================================+==============================================================+
| ``navigation.yaml``               | Navigation2 configuration including planners, controllers,   |
|                                   | costmaps and behavior tree settings.                         |
+-----------------------------------+--------------------------------------------------------------+
| ``amcl_localization.yaml``        | Configuration of the Adaptive Monte Carlo Localization       |
|                                   | (AMCL) node.                                                 |
+-----------------------------------+--------------------------------------------------------------+
| ``slam_toolbox_localization.yaml``| Configuration of SLAM Toolbox in localization mode.          |
+-----------------------------------+--------------------------------------------------------------+
| ``slam_toolbox_mapping.yaml``     | Configuration of SLAM Toolbox for creating occupancy         |
|                                   | grid maps.                                                   |
+-----------------------------------+--------------------------------------------------------------+

Configuration Files
-------------------

navigation.yaml
^^^^^^^^^^^^^^^

This file contains the complete Navigation2 configuration of the MensaBot. It defines the behavior of the global planner, local controller, costmaps, recovery behaviors and additional Navigation2 components.

Repository:
`navigation.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_navigation/config/navigation.yaml>`_

amcl_localization.yaml
^^^^^^^^^^^^^^^^^^^^^^

This file configures the Adaptive Monte Carlo Localization (AMCL) algorithm. It defines the localization parameters used to estimate the robot pose within an existing occupancy grid map.

Repository:
`amcl_localization.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_navigation/config/amcl_localization.yaml>`_

slam_toolbox_localization.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This file configures SLAM Toolbox in localization mode. It is used to localize the robot within an existing map using the SLAM Toolbox localization pipeline.

Repository:
`slam_toolbox_localization.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_navigation/config/slam_toolbox_localization.yaml>`_

slam_toolbox_mapping.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^

This file configures SLAM Toolbox in mapping mode. It defines the parameters used while generating new occupancy grid maps.

Repository:
`slam_toolbox_mapping.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_navigation/config/slam_toolbox_mapping.yaml>`_

Further Documentation
---------------------

A detailed description of the navigation architecture, localization pipeline, mapping process and configuration can be found in the project documentation.

Project Documentation:

`Navigation Documentation <https://github.com/FabCode288/HSK-Mensabot/blob/main/docs/navigation/README.md>`_

Repository:

`mensabot_navigation/config <https://github.com/FabCode288/HSK-Mensabot/tree/main/src/mensabot_navigation/config>`_