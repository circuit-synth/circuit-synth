Circuit Synth Documentation
============================

Circuit Synth is a Python library for programmatic circuit design and KiCad project generation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api
   examples
   contributing

Overview
--------

Circuit Synth provides a high-level, Pythonic interface for designing electronic circuits and generating KiCad projects. It allows you to define circuits using Python code, automatically handle component placement, and generate professional-quality KiCad schematics and PCB layouts.

**Current Status**: Circuit-synth is ready for professional use with the following capabilities:

* Places components functionally (not yet optimized for intelligent board layout)
* Places schematic parts (without intelligent placement algorithms)  
* Generates working KiCad projects suitable for professional development

Key Features
------------

* **Pythonic Circuit Design**: Define circuits using intuitive Python classes and decorators
* **KiCad Integration**: Generate KiCad schematics and PCB layouts automatically
* **Component Management**: Built-in component library with easy extensibility
* **Smart Placement**: Automatic component placement algorithms
* **Type Safety**: Full type hints support for better IDE integration
* **Extensible Architecture**: Clean interfaces for custom implementations

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`