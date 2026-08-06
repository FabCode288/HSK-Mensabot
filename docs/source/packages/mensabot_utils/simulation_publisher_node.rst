Simulation Publisher Node
=========================

The ``SafetySimInputs`` node provides simulated safety hardware signals for the HSK-MensaBot simulation environment.

Instead of requiring physical safety hardware, the node periodically publishes simulated hardware connection and LiDAR safety scanner messages. This allows the complete safety software stack, including the Safety Control Node, to operate without modification during simulation.

Purpose
-------

The node performs the following tasks:

* Simulates the hardware connection state.
* Simulates the front LiDAR safety scanner.
* Simulates the rear LiDAR safety scanner.
* Publishes predefined safety scanner monitoring fields.
* Enables the complete safety architecture to operate unchanged in simulation.

Published Topics
----------------

+---------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| Topic                           | Message Type                                    | Description                                                  |
+=================================+=================================================+==============================================================+
| ``/hardware/connected``         | ``std_msgs/Bool``                               | Simulated hardware connection state.                         |
+---------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``/lidars/front/output_paths``  | ``sick_safetyscanners2_interfaces/OutputPaths`` | Simulated front LiDAR safety scanner data.                   |
+---------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``/lidars/rear/output_paths``   | ``sick_safetyscanners2_interfaces/OutputPaths`` | Simulated rear LiDAR safety scanner data.                    |
+---------------------------------+-------------------------------------------------+--------------------------------------------------------------+

Simulation Behaviour
--------------------

The node periodically publishes predefined safety states for both LiDAR safety scanners. By modifying the internal simulation variables, warning and protective field violations can be emulated without requiring physical hardware.

The published messages include:

* Hardware connection state
* Protective field status
* Warning field status
* Active monitoring case

Related Documentation
---------------------

The simulation environment and the simulated safety architecture are described in the project documentation.

Project Documentation

`Simulation Documentation <https://github.com/FabCode288/HSK-Mensabot/blob/main/docs/simulation/README.md>`_

Repository

`Simulation Publisher Node <https://github.com/FabCode288/HSK-Mensabot/blob/main/src/mensabot_utils/mensabot_utils/simulation_publisher_node.py>`_

API Reference
-------------

.. automodule:: mensabot_utils.simulation_publisher_node
   :members:
   :undoc-members:
   :show-inheritance: