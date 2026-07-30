Safety
======

The Safety module contains the software-based safety components of the HSK-MensaBot.

These components complement the certified hardware safety system by supervising the robot state, selecting the active LiDAR monitoring fields and providing maintenance utilities for the safety scanners. Together, they ensure consistent interaction between the navigation system, the safety hardware and the robot controller.

Components
----------

The Safety module consists of the following components:

**Safety Control Node**

The central software safety component responsible for monitoring the emergency stop state, evaluating the safety scanner outputs and limiting robot motion according to the current safety state.

**LiDAR Field Selection Node**

Selects the active LiDAR monitoring field based on the commanded robot motion and publishes the corresponding dynamic robot footprint for the local Nav2 costmap.

**LiDAR Reset Utility**

Standalone maintenance utility used to perform a hardware reset of the connected LiDAR safety scanners.

.. toctree::
   :maxdepth: 1

   safety_control_node
   lidar_field_selection_node
   lidar_reset