Build
=====

Requirements
------------

The project is developed using Ubuntu 24.04 LTS and ROS 2 Jazzy Jalisco.

Build Workspace
---------------

.. code-block:: bash

   colcon build --symlink-install

Source Workspace
----------------

.. code-block:: bash

   source install/setup.bash

Clean Build
-----------

.. code-block:: bash

   rm -rf build install log
   colcon build --symlink-install