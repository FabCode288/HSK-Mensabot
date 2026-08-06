Mensabot Hardware
=================

The ``mensabot_hardware`` package implements the hardware interface of the MensaBot.

It provides the connection between the ROS 2 control framework and the Arduino-based motor controller. Besides transmitting wheel velocity commands, the hardware interface supervises the communication state, heartbeat monitoring, emergency stop handling and packet-based serial communication. :contentReference[oaicite:0]{index=0}

Package Overview
----------------

The package consists of the following main components:

* **Hardware Interface** implementing the ``hardware_interface::SystemInterface``
* **Serial communication** between Raspberry Pi and Arduino
* **Communication state machine**
* **Emergency stop handling**
* **Heartbeat monitoring**
* **Packet encoding and validation**

Class Reference
---------------

The complete C++ API is generated automatically from the documented source code.

.. doxygenclass:: mensabot_hardware::MensabotHardware
   :members:
   :protected-members:
   :undoc-members:

Communication Protocol
----------------------

The communication protocol is documented in the project repository.

`Communication Protocol Documentation <https://github.com/FabCode288/HSK-Mensabot/tree/main/docs/communication>`_