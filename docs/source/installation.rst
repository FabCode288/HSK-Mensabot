Installation
============

This section describes the basic installation procedure for the MensaBot software.

Requirements
------------

The software has been developed and tested with the following environment.

================== =====================
Operating System   Ubuntu 24.04 LTS
ROS Distribution   ROS 2 Jazzy Jalisco
Simulation         Gazebo Harmonic
Build System       colcon
================== =====================

Clone the Repository
--------------------

Create a new ROS 2 workspace and clone the MensaBot repository.

.. code-block:: bash

   mkdir -p ~/ros2_mensabot_ws/

   git clone https://github.com/FabCode288/HSK-Mensabot.git

Build the Workspace
-------------------

Build the workspace using ``colcon``.

.. code-block:: bash

   cd ~/ros2_mensabot_ws

   colcon build --symlink-install

Source the Workspace
--------------------

After a successful build, source the workspace before using any ROS 2 packages.

.. code-block:: bash

   source install/setup.bash

To source the workspace automatically in every terminal session, add the following line to your shell configuration.

.. code-block:: bash

   echo "source ~/ros2_mensabot_ws/install/setup.bash" >> ~/.bashrc
   source ~/.bashrc