# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(
    0,
    os.path.abspath("../../src")
)

project = 'Mensabot'
copyright = '2026, Fabian K'
author = 'Fabian K'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "breathe",
]
templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

autodoc_mock_imports = [
    "rclpy",
    "geometry_msgs",
    "sensor_msgs",
    "nav_msgs",
    "std_msgs",
    "builtin_interfaces",
    "tf2_ros",
    "numpy",
    "yaml",
    "gpiod",
    "PyQt6",
    "pyqtgraph",

    "action_msgs",
    "nav2_msgs",
    "nav2_msgs.msg",
    "sick_safetyscanners2_interfaces",
    "sick_safetyscanners2_interfaces.msg",
]

autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

breathe_projects = {
    "Mensabot": "../build/doxygen/xml"
}

breathe_default_project = "Mensabot"