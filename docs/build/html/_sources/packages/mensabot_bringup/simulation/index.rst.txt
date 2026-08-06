Simulation Launch Files
=======================

This section documents all launch files available for operating the MensaBot in the Gazebo simulation.

The launch files are organized according to different operating modes. Depending on the desired application, they can be used to start only the simulated robot, localization, navigation, mapping, or the complete simulation environment.

Available Launch Files
----------------------

+-----------------------------------------------+--------------------------------------------------------------+
| Launch File                                   | Description                                                  |
+===============================================+==============================================================+
| ``sim_bringup_robot.launch.py``               | Starts the simulated robot and simulated hardware            |
|                                               | interfaces without localization or navigation.               |
+-----------------------------------------------+--------------------------------------------------------------+
| ``sim_complete_bringup.launch.py``            | Starts the complete simulation including Gazebo,             |
|                                               | localization and autonomous navigation.                      |
+-----------------------------------------------+--------------------------------------------------------------+
| ``localization_sim_amcl.launch.py``           | Starts AMCL localization using an existing map.              |
+-----------------------------------------------+--------------------------------------------------------------+
| ``navigation_sim.launch.py``                  | Starts autonomous navigation using a previously created map. |
+-----------------------------------------------+--------------------------------------------------------------+
| ``navigation_sim_slam.launch.py``             | Starts autonomous navigation while simultaneously            |
|                                               | generating a map using SLAM Toolbox.                         |
+-----------------------------------------------+--------------------------------------------------------------+
| ``mapping_sim.launch.py``                     | Starts SLAM Toolbox for creating a new map.                  |
+-----------------------------------------------+--------------------------------------------------------------+

Launch Commands
---------------

**Bringup**

.. code-block:: bash

   ros2 launch mensabot_bringup sim_bringup_robot.launch.py

**Complete Bringup**

.. code-block:: bash

   ros2 launch mensabot_bringup sim_complete_bringup.launch.py

**Localization**

.. code-block:: bash

   ros2 launch mensabot_bringup localization_sim_amcl.launch.py

**Navigation**

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_sim.launch.py

**Navigation with SLAM**

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_sim_slam.launch.py

**Mapping**

.. code-block:: bash

   ros2 launch mensabot_bringup mapping_sim.launch.py

Detailed Documentation
----------------------

The following pages describe each launch file in detail, including its purpose, launch arguments, included launch files, started nodes and configuration.

.. toctree::
   :maxdepth: 1

   sim_bringup_robot
   sim_complete_bringup
   localization_sim_amcl
   navigation_sim
   navigation_sim_slam
   mapping_sim