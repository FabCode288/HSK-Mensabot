real_complete_bringup.launch.py
===============================

Overview
--------

The ``real_complete_bringup.launch.py`` launch file starts the complete software stack required for autonomous operation of the physical MensaBot.

It combines hardware initialization, localization and autonomous navigation into a single launch file.

Launch Command
--------------

.. code-block:: bash

   ros2 launch mensabot_bringup real_complete_bringup.launch.py

Purpose
-------

This launch file is intended for:

* Complete robot startup
* Autonomous robot operation
* System demonstrations
* End-to-end testing

Started Components
------------------

The launch file starts all software components required for autonomous operation of the physical robot.

Launch Arguments
----------------

This launch file currently provides no user-configurable launch arguments.

Related Configuration
---------------------

The behavior of the complete software stack is configured through the corresponding hardware, localization and Navigation2 parameter files.