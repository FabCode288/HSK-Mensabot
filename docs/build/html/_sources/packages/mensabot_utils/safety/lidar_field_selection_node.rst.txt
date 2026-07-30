LiDAR Field Selection Node
==========================

The ``LidarFieldSelector`` node automatically selects the active LiDAR monitoring field based on the current robot motion. It evaluates the commanded robot velocity, updates the safety scanner field selection via GPIO outputs and publishes a matching dynamic robot footprint for the local Nav2 costmap.

The node ensures that the active safety scanner configuration and the navigation footprint remain synchronized. In addition, it supports a manual override mode for recovery situations and automatically returns to the default monitoring state if command or override timeouts occur.

Purpose
-------

The node performs the following tasks:

* Determines the current robot motion state from commanded velocities.
* Selects the corresponding LiDAR monitoring field.
* Controls the GPIO outputs connected to the safety scanners.
* Publishes the active monitoring state.
* Publishes a dynamic robot footprint for the local Nav2 costmap.
* Supports manual override mode for recovery procedures.
* Monitors command and manual override timeouts.

Subscribed Topics
-----------------

+------------------------------------------+---------------------------------+------------------------------------------------------------------+
| Topic                                    | Message Type                    | Description                                                      |
+==========================================+=================================+==================================================================+
| ``/mensabot_base_controller/cmd_vel_out``| ``geometry_msgs/TwistStamped``  | Velocity commands used to determine the active monitoring field. |
+------------------------------------------+---------------------------------+------------------------------------------------------------------+
| ``/safety/manual_override``              | ``std_msgs/Bool``               | Enables or disables manual override mode.                        |
+------------------------------------------+---------------------------------+------------------------------------------------------------------+

Published Topics
----------------

+------------------------------+---------------------------+-------------------------------------------------------------+
| Topic                        | Message Type              | Description                                                 |
+==============================+===========================+=============================================================+
| ``/safety/field_state``      | ``std_msgs/String``       | Currently active LiDAR monitoring state.                    |
+------------------------------+---------------------------+-------------------------------------------------------------+
| ``/local_costmap/footprint`` | ``geometry_msgs/Polygon`` | Dynamic robot footprint used by the local Nav2 costmap.     |
+------------------------------+---------------------------+-------------------------------------------------------------+

Parameters
----------

+----------------+---------+-----------------------------------------------------------------------------------+
| Parameter      | Default | Description                                                                       |
+================+=========+===================================================================================+
| ``simulation`` | ``true``| Enables simulation mode by disabling GPIO communication with the safety scanners. |
+----------------+---------+-----------------------------------------------------------------------------------+

Monitoring States
-----------------

The node supports the following monitoring states:

* ``STOP``
* ``FORWARD``
* ``BACKWARD``
* ``ROTATE_LEFT``
* ``ROTATE_RIGHT``
* ``MANUAL_OVERRIDE``

Each monitoring state activates the corresponding LiDAR monitoring field and publishes a matching robot footprint for collision checking.

Related Documentation
---------------------

The dynamic safety field concept and the synchronization between the active LiDAR monitoring field and the navigation footprint are described in the project documentation.

Project Documentation

`Safety Documentation <https://github.com/FabCode288/HSK-Mensabot/blob/main/docs/safety/README.md>`_

Repository

`LiDAR Field Selection Node <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_utils/mensabot_utils/lidar_field_selection_node.py>`_

API Reference
-------------

.. automodule:: mensabot_utils.lidar_field_selection_node
   :members:
   :undoc-members:
   :show-inheritance: