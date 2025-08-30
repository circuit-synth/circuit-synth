"""
AC Analysis Plugin for Circuit-Synth Simulation

This plugin provides AC frequency domain analysis functionality.
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


class ACAnalysisPlugin(AnalysisPlugin):
    """Plugin for AC frequency domain analysis."""
    
    @property
    def name(self) -> str:
        return "ac"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate AC analysis configuration."""
        if not isinstance(config, dict):
            return False
        
        # Check required parameters
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            return False
            
        # Validate frequency parameters if present
        freq_params = ['start_frequency', 'stop_frequency']
        for param in freq_params:
            if param in config:
                if not isinstance(config[param], (str, int, float)):
                    return False
        
        if 'points_per_decade' in config:
            if not isinstance(config['points_per_decade'], int) or config['points_per_decade'] <= 0:
                return False
                
        if 'variation' in config:
            if config['variation'] not in ['dec', 'oct', 'lin']:
                return False
                
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for AC analysis."""
        return {
            'enabled': True,
            'start_frequency': '1Hz',
            'stop_frequency': '1MHz', 
            'points_per_decade': 10,
            'variation': 'dec',  # decade, octave, or linear
            'include_phase': True,
            'include_magnitude': True
        }
    
    def prepare_analysis(self, circuit_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare AC analysis parameters."""
        # Merge default config with user config
        full_config = self.get_default_config()
        full_config.update(config.get('ac', {}))
        
        # Validate frequency range
        start_freq = self._parse_frequency(full_config['start_frequency'])
        stop_freq = self._parse_frequency(full_config['stop_frequency'])
        
        if start_freq >= stop_freq:
            raise ValueError(f"Start frequency ({start_freq}) must be less than stop frequency ({stop_freq})")
        
        return {
            'analysis_type': 'ac',
            'circuit_data': circuit_data,
            'config': full_config,
            'backend_config': config.get('circuit_simulation', {}),
            'frequency_params': {
                'start': start_freq,
                'stop': stop_freq,
                'points_per_decade': full_config['points_per_decade'],
                'variation': full_config['variation']
            }
        }
    
    def execute_analysis(self, prepared_params: Dict[str, Any]) -> Any:
        """Execute AC analysis using circuit-simulation backend."""
        circuit_data = prepared_params['circuit_data']
        analysis_config = prepared_params['config']
        backend_config = prepared_params['backend_config']
        freq_params = prepared_params['frequency_params']
        
        logger.info(f"Starting AC analysis: {freq_params['start']:.2e}Hz to {freq_params['stop']:.2e}Hz")
        
        try:
            # Import circuit-simulation directly
            import sys
            backend_path = Path(backend_config.get('backend_path', '../../../'))
            circuit_sim_path = backend_path / 'src'
            
            if str(circuit_sim_path) not in sys.path:
                sys.path.insert(0, str(circuit_sim_path))
            
            from circuit_sim.circuit_synth_integration import simulate_from_circuit_synth
            
            # Call circuit-simulation integration directly
            logger.debug("Calling circuit-simulation AC analysis...")
            results = simulate_from_circuit_synth(circuit_data, analysis_type="ac")
            
            # Convert results to dict format
            results_dict = {
                'analysis_type': 'ac',
                'success': True,
                'frequency': [],
                'magnitude': [],
                'phase': [],
                'frequency_range': {
                    'start': freq_params['start'],
                    'stop': freq_params['stop'],
                    'points_per_decade': freq_params['points_per_decade']
                }
            }
            
            # Extract frequency response data
            if hasattr(results, 'get_frequency_data'):
                freq_data = results.get_frequency_data()
                if freq_data:
                    results_dict.update(freq_data)
            elif hasattr(results, 'frequency') and hasattr(results, 'magnitude'):
                # Direct access to frequency data
                results_dict['frequency'] = list(results.frequency)
                results_dict['magnitude'] = list(results.magnitude)
                if hasattr(results, 'phase'):
                    results_dict['phase'] = list(results.phase)
            
            logger.info(f"AC analysis completed successfully")
            return results_dict
                
        except Exception as e:
            logger.error(f"AC analysis failed: {e}")
            # Return error in expected format
            return {
                'analysis_type': 'ac',
                'success': False,
                'error': str(e),
                'frequency': [],
                'magnitude': [],
                'phase': []
            }
    
    def _parse_frequency(self, freq_str: str) -> float:
        """Parse frequency string to float value in Hz."""
        if isinstance(freq_str, (int, float)):
            return float(freq_str)
            
        freq_str = str(freq_str).strip().upper()
        
        # Parse unit suffixes
        multipliers = {
            'HZ': 1.0,
            'KHZ': 1e3,
            'MHZ': 1e6,
            'GHZ': 1e9,
            'K': 1e3,
            'M': 1e6,
            'G': 1e9
        }
        
        for suffix, mult in multipliers.items():
            if freq_str.endswith(suffix):
                freq_val = float(freq_str[:-len(suffix)])
                return freq_val * mult
        
        # No suffix, assume Hz
        return float(freq_str)