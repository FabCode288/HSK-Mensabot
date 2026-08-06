Real Launch Files
=================


This section documents all launch files available for operating the physical MensaBot.

The launch files are organized according to different operating modes. Depending on the desired application, they can be used to start only the hardware, localization, navigation, mapping, or the complete software stack.

Available Launch Files
----------------------

+-----------------------------------------------+--------------------------------------------------------------+
| Launch File                                   | Description                                                  |
+===============================================+==============================================================+
| ``real_bringup_robot.launch.py``              | Starts the robot hardware and all required hardware          |
|                                               | components without localization or navigation.               |
+-----------------------------------------------+--------------------------------------------------------------+
| ``real_complete_bringup.launch.py``           | Starts the complete software stack including hardware,       |
|                                               | localization and autonomous navigation.                      |
+-----------------------------------------------+--------------------------------------------------------------+
| ``localization_real_amcl.launch.py``          | Starts AMCL localization using an existing map.              |
+-----------------------------------------------+--------------------------------------------------------------+
| ``navigation_real.launch.py``                 | Starts autonomous navigation using a previously created map. |
+-----------------------------------------------+--------------------------------------------------------------+
| ``mapping_real.launch.py``                    | Starts SLAM Toolbox for creating a new map.                  |
+-----------------------------------------------+--------------------------------------------------------------+
| ``real_rviz.launch.py``                       | Starts RViz using the predefined visualization               |
|                                               | configuration.                                               |
+-----------------------------------------------+--------------------------------------------------------------+

Launch Commands
---------------

**Bringup**

.. code-block:: bash

   ros2 launch mensabot_bringup real_bringup_robot.launch.py

**Complete Bringup**

.. code-block:: bash

   ros2 launch mensabot_bringup real_complete_bringup.launch.py

**Localization**

.. code-block:: bash

   ros2 launch mensabot_bringup localization_real_amcl.launch.py

**Navigation**

.. code-block:: bash

   ros2 launch mensabot_bringup navigation_real.launch.py

**Mapping**

.. code-block:: bash

   ros2 launch mensabot_bringup mapping_real.launch.py

**RViz**

.. code-block:: bash

   ros2 launch mensabot_bringup real_rviz.launch.py

Detailed Documentation
----------------------

The following pages describe each launch file in detail, including its purpose, launch arguments, included launch files, started nodes and configuration.

.. toctree::
   :maxdepth: 1

   real_bringup_robot
   real_complete_bringup
   localization_real_amcl
   navigation_real
   mapping_real
   real_rviz