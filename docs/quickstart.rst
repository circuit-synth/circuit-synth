Quick Start
===========

This guide will get you up and running with Circuit-Synth in just a few minutes!

.. note::
   **New to Circuit-Synth?** This page shows you how to create your first circuit in under 5 minutes. 
   For more complex examples, see our :doc:`examples` page.

Basic LED Circuit Example
-------------------------

Let's start with a simple LED circuit that demonstrates the core concepts:

.. raw:: html

   <div class="circuit-schematic">
   <pre>
        3.3V ──┬── R1 (330Ω) ──┬── D1 (LED) ── GND
               │                │
               └── Power Input  └── Current Limiting
   </pre>
   </div>

Here's how to implement this circuit in Circuit-Synth:

.. code-block:: python

   from circuit_synth import Circuit, Component, Net, circuit

   @circuit(name="simple_led")
   def simple_led():
       """
       Simple LED circuit with current limiting resistor.
       Perfect for getting started with Circuit-Synth!
       """
       
       # Create power nets
       VCC_3V3 = Net('VCC_3V3')
       GND = Net('GND')
       
       # Create LED component  
       led = Component(
           symbol="Device:LED", 
           ref="D", 
           value="Red",
           footprint="LED_SMD:LED_0603_1608Metric"
       )
       
       # Create current limiting resistor
       resistor = Component(
           symbol="Device:R", 
           ref="R", 
           value="330",
           footprint="Resistor_SMD:R_0603_1608Metric"
       )
       
       # Make connections
       VCC_3V3 += resistor[1]     # Power to resistor
       resistor[2] += led[1]      # Resistor to LED anode
       led[2] += GND              # LED cathode to ground

   # Generate KiCad files
   if __name__ == '__main__':
       circuit = simple_led()
       circuit.generate_kicad_project("my_first_circuit")
       print("Circuit generated! Check the 'my_first_circuit' folder.")

Core Concepts
-------------

Components
~~~~~~~~~~

Components are the building blocks of your circuits. Each component needs four key properties:

.. raw:: html

   <div class="circuit-component">
   <strong>Component Structure:</strong><br>
   <strong>symbol</strong>: KiCad library symbol<br>
   <strong>ref</strong>: Reference prefix (R, C, U, etc.)<br>
   <strong>value</strong>: Component value/name<br>
   <strong>footprint</strong>: Physical package for PCB
   </div>

.. code-block:: python

   # Standard 10kΩ resistor (0603 package)
   resistor = Component(
       symbol="Device:R",              # KiCad symbol
       ref="R",                        # Reference prefix  
       value="10K",                    # Resistance value
       footprint="Resistor_SMD:R_0603_1608Metric"  # Physical footprint
   )

Nets
~~~~

Nets represent electrical connections (wires) between components:

.. raw:: html

   <div class="net-connection">
   <strong>Tip:</strong> Use descriptive net names like 'VCC_3V3' instead of 'Net1'
   </div>

.. code-block:: python

   # Power and ground nets
   VCC_3V3 = Net('VCC_3V3')     # 3.3V power supply
   VCC_5V = Net('VCC_5V')       # 5V power supply  
   GND = Net('GND')             # Ground reference
   
   # Signal nets
   SPI_MOSI = Net('SPI_MOSI')   # SPI data line
   USB_DP = Net('USB_DP')       # USB D+ signal

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

Circuit-Synth excels at building complex systems from reusable building blocks:

.. tip::
   **Professional Practice:** Keep one circuit per file for better organization and reusability.

.. code-block:: python

   # power_supply.py - Reusable 3.3V regulator
   @circuit(name="ldo_3v3")
   def ldo_3v3_regulator(vin, vout, gnd):
       """3.3V linear regulator with decoupling caps"""
       regulator = Component("Regulator_Linear:AMS1117-3.3", ref="U")
       # ... implementation details
   
   # led_indicators.py - Reusable LED circuit  
   @circuit(name="status_led")
   def status_led(vcc, gnd, control_signal):
       """LED with current limiting resistor"""
       # ... implementation details
   
   # main_board.py - Complete system
   @circuit(name="esp32_dev_board") 
   def esp32_development_board():
       """Complete ESP32 board with power and LEDs"""
       VIN_5V = Net('VIN_5V')
       VCC_3V3 = Net('VCC_3V3') 
       GND = Net('GND')
       
       # Compose subsystems
       ldo_3v3_regulator(VIN_5V, VCC_3V3, GND)  # Power supply
       status_led(VCC_3V3, GND, esp32_gpio)     # Status indicator
       # ... ESP32 and other circuits

.. raw:: html

   <div class="circuit-schematic">
   <pre>
   Hierarchical Project Structure:
   ├── components.py      # Reusable parts library
   ├── power_supply.py    # Voltage regulators  
   ├── led_indicators.py  # Status LEDs
   └── main_board.py      # System integration
   </pre>
   </div>

Next Steps
----------

Ready to dive deeper? Here's your learning path:

.. raw:: html


**What to explore next:**

* :doc:`examples` - Complete ESP32, STM32, and power supply projects
* :doc:`api` - Comprehensive API documentation and advanced features  
* :doc:`contributing` - Help make Circuit-Synth even better
* **GitHub Issues** - Report bugs or request features

.. note::
   **Stuck?** Join our community discussions or file an issue on GitHub. 
   We're here to help you succeed with Circuit-Synth!