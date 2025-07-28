# FILE: src/circuit_synth/kicad/symbol_lib_parser_manager.py

import logging
import os
import threading
from typing import Dict, Optional

from .symbol_lib_parser import KicadSymbol, KicadSymbolParser

logger = logging.getLogger(__name__)


class SharedParserManager:
    """
    Singleton manager for KiCad symbol parser.
    """

    _parser_instance: Optional[KicadSymbolParser] = None
    _lock = threading.Lock()
    _test_mode: bool = False

    @classmethod
    def get_parser(cls, test_mode: bool = False) -> KicadSymbolParser:
        """
        Get or create the shared parser instance.
        If test_mode is True, we avoid reading from system env, or you can
        apply special test logic.
        """
        with cls._lock:
            if cls._parser_instance is None:
                logger.debug(
                    "SharedParserManager: Creating new KicadSymbolParser instance."
                )
                cls._parser_instance = KicadSymbolParser()
            cls._test_mode = test_mode
            return cls._parser_instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset the parser manager state.
        """
        with cls._lock:
            cls._parser_instance = None
            cls._test_mode = False
            logger.debug("SharedParserManager: Reset complete.")
