Contributing
============

.. note::
   This page has been moved. Please see :doc:`CONTRIBUTING` for the full contribution guide.

Development Setup
-----------------

1. Fork and clone the repository
2. Install with development dependencies:

   .. code-block:: bash
   
      # Using uv (recommended)
      uv pip install -e ".[dev]"
      
      # Using pip
      pip install -e ".[dev]"

3. Make your changes
4. Run tests and quality checks:

   .. code-block:: bash
   
      # Format code
      black src/
      isort src/
      
      # Run tests
      uv run pytest
      
      # Type checking
      mypy src/

5. Submit a pull request

Areas for Contribution
----------------------

High Priority
~~~~~~~~~~~~

* **Intelligent Component Placement**: Improve PCB and schematic placement algorithms
* **KiCad Integration**: Enhance compatibility and features
* **Documentation**: More examples and tutorials

Other Areas
~~~~~~~~~~~

* Performance optimization
* Test coverage improvement
* Platform compatibility
* Integration with other EDA tools

Code Style
----------

* Follow PEP 8 guidelines
* Use Black for formatting
* Include type hints
* Write comprehensive docstrings
* Add tests for new features

Getting Help
------------

* **GitHub Issues**: Report bugs and request features
* **GitHub Discussions**: Ask questions and share ideas
* **Documentation**: This documentation site