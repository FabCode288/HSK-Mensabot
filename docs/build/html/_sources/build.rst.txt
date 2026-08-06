Build
=====

This section describes the basic build workflow for the HSK-MensaBot software project. The project is implemented as a standard ROS 2 workspace and uses the ``colcon`` build system.

Requirements
------------

The development environment is based on the following software:

* Ubuntu 24.04 LTS
* ROS 2 Jazzy Jalisco
* Python 3
* ``colcon`` build tools
* All required ROS 2 package dependencies installed

Build Workspace
---------------

Compile all packages within the workspace:

.. code-block:: bash

   colcon build --symlink-install

Source Workspace
----------------

After a successful build, source the workspace before running any ROS 2 commands:

.. code-block:: bash

   source install/setup.bash

Clean Build
-----------

To perform a clean rebuild, remove all generated files before compiling again:

.. code-block:: bash

   rm -rf build install log
   colcon build --symlink-install

Build Documentation
-------------------

Generate the HTML documentation:

.. code-block:: bash

   make html

If the C++ API documentation is used, generate the Doxygen XML files before building Sphinx:

.. code-block:: bash

   doxygen Doxyfile
   make html