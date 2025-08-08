# Try to import Rust-integrated generator first, fallback to Python
try:
    from .rust_integrated_generator import SchematicGenerator
    USING_RUST = True
except ImportError:
    from .main_generator import SchematicGenerator
    USING_RUST = False

from .schematic_writer import write_schematic_file

__all__ = [
    "SchematicGenerator",
    "write_schematic_file",
]

# Log which backend is being used
import logging
logger = logging.getLogger(__name__)
logger.info(f"KiCad schematic generator backend: {'Rust-integrated' if USING_RUST else 'Python-only'}")
