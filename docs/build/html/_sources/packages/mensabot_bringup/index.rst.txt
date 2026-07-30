mensabot_bringup
================

The ``mensabot_bringup`` package contains all launch files required to start the MensaBot software in both simulation and on the physical robot.

To simplify development and maintenance, the launch files are separated into dedicated directories for **Real** and **Simulation**. Both operating modes share nearly the same software architecture while replacing only the hardware-dependent components.

Launch Structure
----------------

The package is divided into two categories:

* **Real** – Launch files for operating the physical robot.
* **Simulation** – Launch files for Gazebo-based simulation.

Operating Modes
---------------

The available launch files support different operating modes:

* Bringup
* Localization
* Navigation
* Mapping
* Complete Bringup

Each operating mode starts a predefined subset of the software stack depending on the desired application.

Parameter Files
---------------

The package also provides configuration files that are shared by multiple launch files.

+---------------------+----------------------------------------------------------+
| File                | Description                                              |
+=====================+==========================================================+
| ``controller.yaml`` | Configuration of the ROS 2 controllers used for robot    |
|                     | motion control.                                          |
+---------------------+----------------------------------------------------------+
| ``ekf.yaml``        | Configuration of the Extended Kalman Filter used for     |
|                     | sensor fusion and odometry estimation.                   |
+---------------------+----------------------------------------------------------+

controller.yaml
^^^^^^^^^^^^^^^

This file configures the controllers used by ``ros2_control``. It defines the available controllers and their parameters for operating the robot.

Repository:

`controller.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_bringup/config/controller.yaml>`_

ekf.yaml
^^^^^^^^

This file configures the Extended Kalman Filter (EKF) used to fuse multiple sensor sources into a single filtered odometry estimate.

Repository:

`ekf.yaml <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_bringup/config/ekf.yaml>`_

Further Documentation
^^^^^^^^^^^^^^^^^^^^^

Additional information about the launch architecture and configuration can be found in the project documentation.

Project Documentation:

`Bringup Documentation <https://github.com/FabCode288/HSK-Mensabot/tree/main/docs/bringup>`_

Configuration Directory:

`mensabot_bringup/config <https://github.com/FabCode288/HSK-Mensabot/tree/main/src/mensabot_bringup/config>`_

Launch Files
------------

.. toctree::
   :maxdepth: 2

   real/index
   simulation/index