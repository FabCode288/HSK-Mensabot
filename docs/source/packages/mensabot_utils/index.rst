mensabot_utils
==============

The ``mensabot_utils`` package contains additional Python-based ROS 2 nodes that extend the functionality of the HSK-MensaBot software stack.

Unlike the core packages responsible for navigation or hardware control, these nodes implement project-specific features such as software safety mechanisms, simulation support, monitoring and command processing. Most of the nodes are started automatically by the corresponding bringup launch files, while the monitoring application can also be executed independently.

Modules
-------

The package is divided into the following functional modules:

**Safety**

Contains nodes implementing software-based safety functions, including safety supervision, dynamic safety field selection and LiDAR reset functionality.

**Simulation**

Provides helper nodes that simulate hardware-specific information unavailable in Gazebo, allowing the software architecture to operate consistently in both simulation and on the physical robot.

**Monitoring**

Contains the graphical MensaMonitor application, which visualizes the current robot state and diagnostic information during development and testing.

**Transformation**

Provides utility nodes for processing ROS 2 messages before they are forwarded to other software components.

.. toctree::
   :maxdepth: 3

   safety/index
   simulation_publisher_node
   mensabot_monitor
   cmd_vel_transform_node