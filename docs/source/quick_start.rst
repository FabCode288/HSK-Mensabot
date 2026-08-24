Quick Start
===========

This section provides the most common commands for starting the MensaBot software in simulation and on the real robot.

Simulation
----------

Start the complete simulation environment including navigation and localization.

.. code-block:: bash

   ros2 launch mensabot_bringup sim_complete_bringup.launch.py

To start only the simulation environment without navigation and localization:

.. code-block:: bash

   ros2 launch mensabot_bringup sim_bringup_robot.launch.py

Real Robot
----------

Start the complete software stack on the robot.

.. code-block:: bash

   ros2 launch mensabot_bringup real_complete_bringup.launch.py

To start only the robot hardware without navigation and localization:

.. code-block:: bash

   ros2 launch mensabot_bringup real_bringup_robot.launch.py

Monitoring
----------

Start the MensaBot Monitor to display diagnostic and debugging information.

.. code-block:: bash

   python3 src/mensabot_utils/mensabot_utils/mensabot_monitor.py