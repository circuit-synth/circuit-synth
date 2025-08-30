"""
DC Analysis Plugin for Circuit-Synth Simulation

This plugin provides DC operating point analysis functionality.
It integrates with the circuit-simulation library backend to perform SPICE simulations.
"""

import logging
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from ...plugin_manager import AnalysisPlugin

logger = logging.getLogger(__name__)


class DCAnalysisPlugin(AnalysisPlugin):
    """Plugin for DC operating point analysis."""
    
    @property
    def name(self) -> str:
        return "dc"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate DC analysis configuration."""
        # DC analysis has minimal configuration requirements
        if not isinstance(config, dict):
            return False
            
        # Check for any DC-specific parameters if present
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            return False
            
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for DC analysis."""
        return {
            'enabled': True,
            'include_operating_point': True,
            'calculate_small_signal': False
        }
    
    def prepare_analysis(self, circuit_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare DC analysis parameters."""
        # Merge default config with user config
        full_config = self.get_default_config()
        full_config.update(config.get('dc', {}))
        
        return {
            'analysis_type': 'dc',
            'circuit_data': circuit_data,
            'config': full_config,
            'backend_config': config.get('circuit_simulation', {})
        }
    
    def execute_analysis(self, prepared_params: Dict[str, Any]) -> Any:
        """Execute DC analysis using circuit-simulation backend."""
        circuit_data = prepared_params['circuit_data']
        analysis_config = prepared_params['config']
        backend_config = prepared_params['backend_config']
        
        logger.info("Starting DC analysis...")
        
        try:
            # Import circuit-simulation directly
            import sys
            backend_path = Path(backend_config.get('backend_path', '../../../'))
            circuit_sim_path = backend_path / 'src'
            
            if str(circuit_sim_path) not in sys.path:
                sys.path.insert(0, str(circuit_sim_path))
            
            from circuit_sim.circuit_synth_integration import simulate_from_circuit_synth
            
            # Call circuit-simulation integration directly
            logger.debug("Calling circuit-simulation integration...")
            results = simulate_from_circuit_synth(circuit_data, analysis_type="dc")
            
            # Convert results to dict format
            results_dict = {
                'analysis_type': 'dc',
                'success': True,
                'voltages': {},
                'currents': {},
                'operating_point': True
            }
            
            # Extract voltage data
            if hasattr(results, 'get_voltages'):
                voltages = results.get_voltages()
                if voltages:
                    results_dict['voltages'] = voltages
                    
            # Extract current data  
            if hasattr(results, 'get_currents'):
                currents = results.get_currents()
                if currents:
                    results_dict['currents'] = currents
            
            logger.info(f"DC analysis completed successfully")
            return results_dict
                
        except Exception as e:
            logger.error(f"DC analysis failed: {e}")
            # Return error in expected format
            return {
                'analysis_type': 'dc',
                'success': False,
                'error': str(e),
                'voltages': {},
                'currents': {}
            }