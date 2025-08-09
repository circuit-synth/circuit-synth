Circuit-Synth Documentation
============================

**Pythonic circuit design for professional KiCad projects**

Circuit-Synth is an open-source Python library that fits seamlessly into normal EE workflows without getting too fancy. Unlike domain-specific languages that require learning new syntax, circuit-synth uses simple, transparent Python code that any engineer can understand and modify.

.. image:: https://img.shields.io/pypi/v/circuit-synth
   :target: https://pypi.org/project/circuit-synth/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/circuit-synth
   :target: https://pypi.org/project/circuit-synth/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/circuit-synth/circuit-synth
   :target: https://github.com/circuit-synth/circuit-synth/blob/main/LICENSE
   :alt: License

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   installation
   quickstart
   examples

.. toctree::
   :maxdepth: 2
   :caption: Architecture & Design:

   ARCHITECTURE
   JSON_SCHEMA
   PROJECT_STRUCTURE

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api

.. toctree::
   :maxdepth: 2
   :caption: Development:

   CONTRIBUTING
   TESTING
   SCRIPT_REFERENCE

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics:

   SIMULATION_SETUP
   test_plan_generation
   integration/CLAUDE_INTEGRATION

Quick Start
-----------

Install Circuit-Synth:

.. code-block:: bash

   pip install circuit-synth

Create your first circuit:

.. code-block:: python

   from circuit_synth import *

   @circuit(name="esp32s3_simple")
   def esp32s3_simple():
       """Simple ESP32-S3 circuit with decoupling capacitor"""
       
       # Create power nets
       _3V3 = Net('3V3')
       GND = Net('GND')
       
       # ESP32-S3 module
       esp32s3 = Component(
           symbol="RF_Module:ESP32-S3-MINI-1",
           ref="U",
           footprint="RF_Module:ESP32-S2-MINI-1"
       )
       
       # Decoupling capacitor
       cap_power = Component(
           symbol="Device:C",
           ref="C", 
           value="10uF",
           footprint="Capacitor_SMD:C_0603_1608Metric"
       )
       
       # Connect components
       _3V3 += esp32s3["VDD"], cap_power[1]
       GND += esp32s3["GND"], cap_power[2]

   # Generate KiCad project
   circuit = esp32s3_simple()
   circuit.generate_kicad_project("my_esp32_project")

Core Principles
---------------

* **Simple Python Code**: No special DSL to learn - just Python classes and functions
* **Transparent to Users**: Generated KiCad files are clean and human-readable  
* **Bidirectional Updates**: KiCad can remain the source of truth - import existing projects and export changes back
* **Normal EE Workflow**: Integrates with existing KiCad-based development processes

Current Capabilities
--------------------

**Circuit-synth is ready for professional use with:**

* **Full KiCad Integration**: Generate complete KiCad projects with schematics and PCB layouts
* **Schematic Annotations**: Automatic docstring extraction and manual text annotations with tables
* **Netlist Generation**: Export industry-standard KiCad netlist files (.net) for seamless PCB workflow
* **Hierarchical Design Support**: Multi-sheet projects with proper organization and connectivity
* **Professional Component Management**: Complete footprint, symbol, and library integration
* **Ratsnest Generation**: Visual airwire connections for unrouted nets
* **Placement Algorithms**: Multiple algorithms for component and schematic placement

Key Features
------------

* **Pythonic Circuit Design**: Define circuits using intuitive Python classes and decorators
* **KiCad Integration**: Generate KiCad schematics and PCB layouts automatically
* **Component Management**: Built-in component library with easy extensibility  
* **Smart Placement**: Multiple automatic component placement algorithms
* **Type Safety**: Full type hints support for better IDE integration
* **Extensible Architecture**: Clean interfaces for custom implementations
* **Professional Output**: Generates production-ready KiCad projects

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`