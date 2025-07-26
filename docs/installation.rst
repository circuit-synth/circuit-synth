Installation
============

Requirements
------------

* Python 3.9 or higher
* KiCad (for project generation)

Installation Methods
--------------------

PyPI Installation (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install circuit-synth

Using uv (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install circuit-synth
   uv pip install circuit-synth
   
   # For development
   uv pip install -e ".[dev]"

From Source
~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/circuitsynth/circuit-synth.git
   cd circuit-synth
   
   # Using uv (recommended)
   uv pip install -e ".[dev]"
   
   # Using pip
   pip install -e ".[dev]"

Verification
~~~~~~~~~~~~

To verify your installation:

.. code-block:: python

   import circuit_synth
   print(circuit_synth.__version__)

KiCad Setup
-----------

Circuit Synth requires KiCad for generating schematic and PCB files. Download and install KiCad from the `official website <https://www.kicad.org/download/>`_.

Make sure KiCad is in your system PATH, or specify the KiCad installation path when configuring Circuit Synth.