# -*- coding: utf-8 -*-
#
# hierarchy_manager.py
#
# This was used in older code to build a hierarchy. Now replaced by circuit_loader's logic.
# We leave a stub for potential expansions.

import logging

logger = logging.getLogger(__name__)


class HierarchyManager:
    def __init__(self, top_circuit):
        logger.debug("HierarchyManager stub init for circuit '%s'", top_circuit.name)
        self.top_circuit = top_circuit
        # not used now

    def build_hierarchy(self):
        logger.debug("HierarchyManager stub: build_hierarchy called.")
        # no-op
