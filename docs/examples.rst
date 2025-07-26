Examples
========

This section contains practical examples demonstrating Circuit Synth capabilities.

Simple LED Circuit
------------------

A basic LED circuit with current limiting resistor:

.. literalinclude:: ../examples/example_kicad_project.py
   :language: python
   :lines: 1-50
   :caption: Basic LED circuit setup

Complex ESP32 Project
----------------------

The main example demonstrates a complex ESP32-based project with multiple subcircuits:

.. literalinclude:: ../examples/example_kicad_project.py
   :language: python
   :lines: 270-320
   :caption: ESP32 main circuit

This example shows:

* Hierarchical circuit design
* Multiple subcircuits (regulator, USB, IMU, debug header)
* Component reuse and templating
* Automatic reference designation
* Net management

Power Supply Circuit
--------------------

A 3.3V linear regulator circuit:

.. literalinclude:: ../examples/example_kicad_project.py
   :language: python
   :lines: 53-82
   :caption: Linear regulator circuit

USB Interface
-------------

USB-C connector with ESD protection:

.. literalinclude:: ../examples/example_kicad_project.py
   :language: python
   :lines: 108-165
   :caption: USB-C interface with protection

IMU Circuit
-----------

SPI-connected IMU with power filtering:

.. literalinclude:: ../examples/example_kicad_project.py
   :language: python
   :lines: 166-198
   :caption: IMU circuit with SPI interface

Running the Examples
--------------------

To run the complete example:

.. code-block:: bash

   # Navigate to the project directory
   cd circuit-synth
   
   # Run the example
   python examples/example_kicad_project.py
   
   # Specify placement algorithm (optional)
   python examples/example_kicad_project.py connection_aware

This will generate:

* ``circuit_synth_example_kicad_project.json`` - Circuit data
* ``circuit_synth_example_kicad_project.net`` - KiCad netlist
* ``kicad_output/`` directory with complete KiCad project files

Placement Algorithms
--------------------

The example supports different placement algorithms:

* ``sequential`` - Simple sequential placement
* ``connection_aware`` - Connection-based optimization (default)
* ``llm`` - AI-powered intelligent placement

Advanced Features
-----------------

Component Templates
~~~~~~~~~~~~~~~~~~~

Define reusable component templates:

.. code-block:: python

   # Define a template
   C_10uF_0805 = Component(
       symbol="Device:C", ref="C", value="10uF",
       footprint="Capacitor_SMD:C_0805_2012Metric"
   )
   
   # Use the template
   cap1 = C_10uF_0805()
   cap1.ref = "C1"

Mixed Pin Access
~~~~~~~~~~~~~~~~

Use both integer and string pin access:

.. code-block:: python

   # Integer pin access
   regulator[1] += GND
   
   # String pin access  
   regulator["VIN"] += input_voltage
   
   # Mixed access
   resistor[1] += regulator["VOUT"]

Debugging and Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable debug features:

.. code-block:: python

   gen.generate_project(
       "circuit.json",
       generate_pcb=True,
       draw_bounding_boxes=True,  # Show component boundaries
       force_regenerate=True      # Overwrite existing files
   )