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

Launch Files
-------------

.. toctree::
   :maxdepth: 2

   real/index
   simulation/index