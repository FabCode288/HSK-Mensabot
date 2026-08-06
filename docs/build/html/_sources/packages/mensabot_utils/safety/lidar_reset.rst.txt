LiDAR Reset Utility
===================

The ``lidar_reset.py`` script performs a hardware reset of the connected LiDAR safety scanners using a dedicated GPIO output.

Unlike the other components in this package, the script is not implemented as a ROS 2 node. Instead, it is intended as a standalone maintenance utility that generates a reset pulse, waits for the LiDAR sensors to reboot and terminates automatically after the reset procedure has completed.

Purpose
-------

The utility performs the following tasks:

* Generates a reset pulse on the dedicated LiDAR reset GPIO.
* Initiates a hardware reboot of the connected LiDAR sensors.
* Waits until the sensors have completed their startup sequence.
* Terminates automatically after the reset process.

Hardware Interface
------------------

The reset signal is generated using a dedicated GPIO output on the Raspberry Pi.

+----------------+-----------------------------------------------+
| Interface      | Description                                   |
+================+===============================================+
| GPIO           | Generates the hardware reset pulse.           |
+----------------+-----------------------------------------------+
| GPIO Chip      | ``/dev/gpiochip4``                            |
+----------------+-----------------------------------------------+
| GPIO Pin       | ``16``                                        |
+----------------+-----------------------------------------------+

Execution
---------

The script can be executed directly from the command line.

.. code-block:: bash

   python3 lidar_reset.py

Related Documentation
---------------------

The LiDAR sensors and their integration into the safety architecture are described in the project documentation.

Project Documentation

`Safety Documentation <https://github.com/FabCode288/HSK-Mensabot/blob/main/docs/safety/README.md>`_

Repository

`LiDAR Reset Utility <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_utils/mensabot_utils/lidar_reset.py>`_

API Reference
-------------

.. automodule:: mensabot_utils.lidar_reset
   :members:
   :undoc-members:
   :show-inheritance: