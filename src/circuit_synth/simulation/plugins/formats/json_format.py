"""
JSON Format Plugin for Circuit-Synth Simulation Reports

This plugin generates machine-readable JSON data exports of simulation results.
Useful for programmatic processing and integration with other tools.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ...plugin_manager import FormatPlugin

logger = logging.getLogger(__name__)


class JSONFormatPlugin(FormatPlugin):
    """Plugin for generating JSON data export."""
    
    @property
    def name(self) -> str:
        return "json"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def file_extension(self) -> str:
        return "json"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate JSON format configuration."""
        if not isinstance(config, dict):
            return False
        
        # Check boolean options
        bool_options = ['pretty_print', 'include_metadata', 'include_circuit_data']
        for option in bool_options:
            if option in config and not isinstance(config[option], bool):
                return False
        
        # Check indent option
        if 'indent' in config:
            if not isinstance(config['indent'], (int, type(None))):
                return False
        
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for JSON format."""
        return {
            'pretty_print': True,
            'indent': 2,
            'include_metadata': True,
            'include_circuit_data': True,
            'include_timestamps': True
        }
    
    def generate_report(self, 
                       circuit_data: Dict[str, Any],
                       analysis_results: Dict[str, Any], 
                       config: Dict[str, Any]) -> str:
        """Generate JSON report and return output file path."""
        
        # Merge default config with user config
        format_config = self.get_default_config()
        format_config.update(config.get('json', {}))
        
        output_config = config.get('output', {})
        
        logger.info("Generating JSON report...")
        
        try:
            # Determine output directory and filename
            output_dir = Path(output_config.get('output_directory', 'simulation_reports'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            circuit_name = circuit_data.get('name', 'circuit')
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"{circuit_name}_data_{timestamp}.json"
            
            # Prepare JSON data structure
            json_data = self._create_json_structure(circuit_data, analysis_results, format_config)
            
            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                if format_config['pretty_print']:
                    json.dump(json_data, f, indent=format_config['indent'], ensure_ascii=False)
                else:
                    json.dump(json_data, f, ensure_ascii=False)
            
            logger.info(f"JSON report generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"JSON report generation failed: {e}")
            raise
    
    def _create_json_structure(self, circuit_data: Dict[str, Any], analysis_results: Dict[str, Any], 
                              format_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create the JSON data structure."""
        
        json_data = {
            "format": "circuit-synth-simulation-report",
            "version": "1.0",
            "analysis_results": analysis_results
        }
        
        # Add metadata if requested
        if format_config.get('include_metadata', True):
            json_data["metadata"] = {
                "generated_by": "circuit-synth",
                "plugin_name": self.name,
                "plugin_version": self.version,
                "generator": "JSONFormatPlugin"
            }
            
            if format_config.get('include_timestamps', True):
                json_data["metadata"]["generated_at"] = datetime.now().isoformat()
        
        # Add circuit data if requested
        if format_config.get('include_circuit_data', True):
            json_data["circuit"] = circuit_data
        
        # Add analysis summary
        json_data["summary"] = {
            "circuit_name": circuit_data.get('name', 'Unknown'),
            "analysis_types": list(analysis_results.keys()),
            "num_analysis_types": len(analysis_results)
        }
        
        # Add analysis-specific summaries
        for analysis_type, results in analysis_results.items():
            summary_key = f"{analysis_type}_summary"
            json_data["summary"][summary_key] = self._create_analysis_summary(analysis_type, results)
        
        return json_data
    
    def _create_analysis_summary(self, analysis_type: str, results: Any) -> Dict[str, Any]:
        """Create summary for a specific analysis type."""
        
        summary = {
            "analysis_type": analysis_type,
            "status": "completed" if results else "failed"
        }
        
        try:
            if isinstance(results, dict):
                # Count data points if available
                if 'voltages' in results:
                    summary["voltage_nodes"] = len(results['voltages']) if isinstance(results['voltages'], dict) else 0
                
                if 'currents' in results:
                    summary["current_measurements"] = len(results['currents']) if isinstance(results['currents'], dict) else 0
                
                # Analysis-specific summaries
                if analysis_type == 'dc':
                    summary["operating_point"] = True
                    
                elif analysis_type == 'ac':
                    if 'frequency' in results:
                        freq_data = results['frequency']
                        if isinstance(freq_data, (list, tuple)) and len(freq_data) > 0:
                            summary["frequency_range"] = {
                                "start": min(freq_data),
                                "stop": max(freq_data),
                                "points": len(freq_data)
                            }
                
                elif analysis_type == 'transient':
                    if 'time' in results:
                        time_data = results['time']
                        if isinstance(time_data, (list, tuple)) and len(time_data) > 0:
                            summary["time_range"] = {
                                "start": min(time_data),
                                "stop": max(time_data),
                                "points": len(time_data)
                            }
                
                # Add data size information
                summary["data_size"] = self._estimate_data_size(results)
                
        except Exception as e:
            summary["summary_error"] = str(e)
        
        return summary
    
    def _estimate_data_size(self, data: Any) -> Dict[str, Any]:
        """Estimate the size of data structures."""
        try:
            json_str = json.dumps(data)
            return {
                "bytes": len(json_str.encode('utf-8')),
                "characters": len(json_str)
            }
        except:
            return {"error": "Could not estimate size"}