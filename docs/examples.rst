Examples
========

This section contains practical examples demonstrating Circuit Synth capabilities.

Simple LED Circuit
------------------

A basic LED circuit with current limiting resistor:

.. literalinclude:: ../example_project/circuit-synth/main.py
   :language: python
   :lines: 1-50
   :caption: Basic LED circuit setup

Complex ESP32 Project
----------------------

The main example demonstrates a complex ESP32-based project with multiple subcircuits:

.. literalinclude:: ../example_project/circuit-synth/main.py
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

.. literalinclude:: ../example_project/circuit-synth/power_supply.py
   :language: python
   :lines: 1-30
   :caption: Linear regulator circuit

USB Interface
-------------

USB-C connector with ESD protection:

.. literalinclude:: ../example_project/circuit-synth/usb.py
   :language: python
   :lines: 1-40
   :caption: USB-C interface with protection

ESP32 Microcontroller
---------------------

ESP32-C6 microcontroller with decoupling:

.. literalinclude:: ../example_project/circuit-synth/esp32c6.py
   :language: python
   :lines: 1-40
   :caption: ESP32 microcontroller circuit

Running the Examples
--------------------

To run the complete example:

.. code-block:: bash

   # Navigate to the project directory
   cd circuit-synth
   
   # Run the example
   python example_project/circuit-synth/main.py
   
   # Generate complete KiCad project
   python example_project/circuit-synth/main.py

This will generate:

* ``ESP32_C6_Dev_Board.json`` - Circuit netlist data
* ``ESP32_C6_Dev_Board/`` directory with complete KiCad project files
  * ``.kicad_pro`` - KiCad project file
  * ``.kicad_sch`` - Schematic file
  * ``.kicad_pcb`` - PCB layout file

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