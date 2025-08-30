"""
Transient Analysis Plugin for Circuit-Synth Simulation

This plugin provides time domain transient analysis functionality.
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


class TransientAnalysisPlugin(AnalysisPlugin):
    """Plugin for transient time domain analysis."""
    
    @property
    def name(self) -> str:
        return "transient"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate transient analysis configuration."""
        if not isinstance(config, dict):
            return False
        
        # Check required parameters
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            return False
            
        # Validate time parameters if present
        time_params = ['duration', 'timestep', 'start_time']
        for param in time_params:
            if param in config:
                if not isinstance(config[param], (str, int, float)):
                    return False
        
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for transient analysis."""
        return {
            'enabled': True,
            'duration': '10ms',
            'timestep': '1us',
            'start_time': '0s',
            'max_timestep': None,  # Let SPICE choose
            'include_initial_conditions': True
        }
    
    def prepare_analysis(self, circuit_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare transient analysis parameters."""
        # Merge default config with user config
        full_config = self.get_default_config()
        full_config.update(config.get('transient', {}))
        
        # Parse time parameters
        duration = self._parse_time(full_config['duration'])
        timestep = self._parse_time(full_config['timestep'])
        start_time = self._parse_time(full_config['start_time'])
        
        # Validate time parameters
        if timestep <= 0:
            raise ValueError(f"Timestep must be positive: {timestep}")
        if duration <= 0:
            raise ValueError(f"Duration must be positive: {duration}")
        if start_time < 0:
            raise ValueError(f"Start time must be non-negative: {start_time}")
        if timestep >= duration:
            raise ValueError(f"Timestep ({timestep}) must be less than duration ({duration})")
        
        return {
            'analysis_type': 'transient',
            'circuit_data': circuit_data,
            'config': full_config,
            'backend_config': config.get('circuit_simulation', {}),
            'time_params': {
                'start': start_time,
                'duration': duration,
                'timestep': timestep,
                'stop': start_time + duration
            }
        }
    
    def execute_analysis(self, prepared_params: Dict[str, Any]) -> Any:
        """Execute transient analysis using circuit-simulation backend."""
        circuit_data = prepared_params['circuit_data']
        analysis_config = prepared_params['config']
        backend_config = prepared_params['backend_config']
        time_params = prepared_params['time_params']
        
        logger.info(f"Starting transient analysis: {time_params['start']:.2e}s to {time_params['stop']:.2e}s, "
                   f"timestep: {time_params['timestep']:.2e}s")
        
        try:
            # Get path to circuit-simulation integration
            backend_path = Path(backend_config.get('backend_path', '../../../'))
            integration_script = backend_path / 'src' / 'circuit_sim' / 'circuit_synth_integration.py'
            
            if not integration_script.exists():
                raise FileNotFoundError(f"Circuit-simulation integration not found at: {integration_script}")
            
            # Create temporary file for circuit data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(circuit_data, f, indent=2)
                temp_file = Path(f.name)
            
            try:
                # Call circuit-simulation backend with transient parameters
                cmd = [
                    'python', str(integration_script),
                    '--input', str(temp_file),
                    '--analysis', 'transient',
                    '--output-format', 'json',
                    '--transient-duration', str(time_params['duration']),
                    '--transient-timestep', str(time_params['timestep']),
                    '--transient-start', str(time_params['start'])
                ]
                
                logger.debug(f"Executing: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=backend_config.get('timeout', 60),  # Longer timeout for transient
                    cwd=backend_path
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Circuit simulation failed: {result.stderr}")
                
                # Parse results
                try:
                    results = json.loads(result.stdout)
                    logger.info(f"Transient analysis completed successfully")
                    return results
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Failed to parse simulation results: {e}")
                    
            finally:
                # Clean up temporary file
                temp_file.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Transient analysis failed: {e}")
            raise
    
    def _parse_time(self, time_str: str) -> float:
        """Parse time string to float value in seconds."""
        if isinstance(time_str, (int, float)):
            return float(time_str)
            
        time_str = str(time_str).strip().upper()
        
        # Parse unit suffixes
        multipliers = {
            'S': 1.0,
            'MS': 1e-3,
            'US': 1e-6,
            'NS': 1e-9,
            'PS': 1e-12,
            'M': 1e-3,  # Assume milliseconds for 'm' suffix
            'U': 1e-6,  # Microseconds
            'N': 1e-9,  # Nanoseconds
            'P': 1e-12  # Picoseconds
        }
        
        for suffix, mult in multipliers.items():
            if time_str.endswith(suffix):
                time_val = float(time_str[:-len(suffix)])
                return time_val * mult
        
        # No suffix, assume seconds
        return float(time_str)