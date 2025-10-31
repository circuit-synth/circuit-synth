Installation
============

Requirements
------------

* Python 3.12 or higher
* KiCad (for project generation)

Installation Methods
--------------------

Using uv (Recommended)
~~~~~~~~~~~~~~~~~~~~~~

Fast package installer with better dependency resolution:

.. code-block:: bash

   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install circuit-synth
   uv add circuit-synth

   # For development
   git clone https://github.com/circuit-synth/circuit-synth.git
   cd circuit-synth
   uv sync

Using pip (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~

Standard Python package installer:

.. code-block:: bash

   pip install circuit-synth

From Source
~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/circuit-synth/circuit-synth.git
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