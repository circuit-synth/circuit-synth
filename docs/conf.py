# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from unittest.mock import MagicMock

# Add the source directory to the path so we can import circuit_synth
sys.path.insert(0, os.path.abspath('../src'))

# Mock modules that might not be available during doc builds
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

MOCK_MODULES = [
    'rust_core_circuit_engine',
    'rust_force_directed_placement',
    'rust_io_processor',
    'rust_kicad_schematic_writer',
    'rust_netlist_processor',
    'rust_pin_calculator',
    'rust_reference_manager',
    'rust_symbol_cache',
    'rust_symbol_search',
]
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

project = 'Circuit-Synth'
copyright = '2025, Circuit Synth Contributors'
author = 'Circuit Synth Contributors'

# Get version from the package
try:
    import circuit_synth
    release = circuit_synth.__version__
    version = '.'.join(release.split('.')[:2])  # Short version (e.g., "0.1")
except (ImportError, AttributeError):
    release = '0.1.0'
    version = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,  # Changed to False to reduce warnings
    'exclude-members': '__weakref__'
}

# Handle import errors gracefully
autodoc_mock_imports = [
    'rust_core_circuit_engine',
    'rust_force_directed_placement',
    'rust_io_processor',
    'rust_kicad_schematic_writer',
    'rust_netlist_processor',
    'rust_pin_calculator',
    'rust_reference_manager',
    'rust_symbol_cache',
    'rust_symbol_search',
]

# Suppress warnings that cause build failures
suppress_warnings = [
    'autodoc.import_object',
    'ref.python',
]

# MyST settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Todo settings
todo_include_todos = True