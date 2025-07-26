Quick Start
===========

This guide will get you up and running with Circuit Synth in just a few minutes.

Basic LED Circuit Example
--------------------------

Here's a simple example that creates an LED circuit and generates KiCad files:

.. code-block:: python

   from circuit_synth import *
   import os

   # Define components
   LED_0603 = Component(
       symbol="Device:LED", ref="D", value="LED",
       footprint="LED_SMD:LED_0603_1608Metric"
   )

   R_330 = Component(
       symbol="Device:R", ref="R", value="330",
       footprint="Resistor_SMD:R_0603_1608Metric"
   )

   # Define a simple LED circuit
   @circuit
   def led_circuit():
       # Create power nets
       _3v3 = Net('3V3')
       GND = Net('GND')
       led_net = Net('LED_NET')
       
       # Create components
       led = LED_0603()
       led.ref = "D1"
       
       resistor = R_330()
       resistor.ref = "R1"
       
       # Connect components using pin access
       resistor[1] += _3v3      # Resistor to power
       resistor[2] += led_net   # Resistor to LED
       led[1] += led_net        # LED anode
       led[2] += GND            # LED cathode

   # Generate KiCad files
   if __name__ == '__main__':
       c = led_circuit()
       
       # Create output directory
       output_dir = "kicad_output"
       os.makedirs(output_dir, exist_ok=True)
       
       # Generate KiCad project
       gen = create_unified_kicad_integration(output_dir, "led_circuit")
       gen.generate_project(
           circuit=c,
           generate_pcb=True,
           force_regenerate=True
       )

Core Concepts
-------------

Components
~~~~~~~~~~

Components are the building blocks of your circuits. Define them with symbols, reference designators, values, and footprints:

.. code-block:: python

   resistor = Component(
       symbol="Device:R",          # KiCad symbol
       ref="R",                    # Reference prefix
       value="10K",               # Component value
       footprint="Resistor_SMD:R_0603_1608Metric"  # KiCad footprint
   )

Nets
~~~~

Nets represent electrical connections between components:

.. code-block:: python

   power_net = Net('VCC')
   ground_net = Net('GND')

Circuits
~~~~~~~~

Use the ``@circuit`` decorator to define circuit functions:

.. code-block:: python

   @circuit
   def my_circuit():
       # Define your circuit here
       pass

Pin Connections
~~~~~~~~~~~~~~~

Connect component pins to nets using indexing:

.. code-block:: python

   # Connect pin 1 of resistor to power net
   resistor[1] += power_net
   
   # Connect pin 2 of resistor to signal net
   resistor[2] += signal_net

Hierarchical Design
-------------------

Circuit Synth supports hierarchical circuit design:

.. code-block:: python

   @circuit(name="Power_Supply")
   def power_supply(vin, vout, gnd):
       # Power supply implementation
       pass

   @circuit
   def main_circuit():
       # Create nets
       _12v = Net('12V')
       _5v = Net('5V')
       gnd = Net('GND')
       
       # Use the power supply subcircuit
       power_supply(_12v, _5v, gnd)

Next Steps
----------

* Explore the :doc:`examples` for more complex circuits
* Read the :doc:`api` documentation for detailed reference
* Check out the :doc:`contributing` guide to help improve Circuit Synth