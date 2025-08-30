"""
Main Simulation Interface for Circuit-Synth

This module provides the new simulate() function that uses the extensible plugin system.
It integrates with the circuit-simulation backend through configurable plugins.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .plugin_manager import get_plugin_registry, get_configuration_manager, AnalysisPlugin, FormatPlugin

logger = logging.getLogger(__name__)


def simulate(circuit,
            analysis: Optional[Union[str, List[str]]] = None,
            config: Optional[Dict[str, Any]] = None,
            format: str = "default") -> str:
    """
    Run simulation analysis on a circuit using the extensible plugin system.
    
    This is the new main simulate() function that provides extensible, plugin-based
    simulation with configurable analysis types and output formats.
    
    Args:
        circuit: Circuit object to simulate
        analysis: Analysis type(s) to run. Can be:
            - None: Run default analysis types from config
            - str: Single analysis type (e.g., "dc", "ac", "transient")
            - List[str]: Multiple analysis types (e.g., ["dc", "ac"])
        config: Optional configuration override. If None, loads from config files.
        format: Output format ("html", "json", or "default")
    
    Returns:
        str: Path to generated report file
        
    Raises:
        ValueError: If analysis type or format not available
        RuntimeError: If simulation or report generation fails
        
    Examples:
        >>> circuit = my_circuit_function()
        >>> report_path = simulate(circuit)  # Run all default analyses, HTML report
        
        >>> report_path = simulate(circuit, analysis="ac")  # AC analysis only
        
        >>> report_path = simulate(circuit, 
        ...                       analysis=["dc", "transient"],
        ...                       format="json")
        
        >>> custom_config = {
        ...     "ac": {"start_frequency": "10Hz", "stop_frequency": "100kHz"},
        ...     "output": {"output_directory": "my_reports"}
        ... }
        >>> report_path = simulate(circuit, config=custom_config)
    """
    
    logger.info(f"Starting simulation for circuit: {circuit.name}")
    
    try:
        # Initialize plugin system
        registry = get_plugin_registry()
        config_manager = get_configuration_manager()
        
        # Load configuration
        if config is None:
            config = config_manager.load_config()
        else:
            # Merge with default config
            default_config = config_manager.load_config()
            merged_config = _deep_merge_config(default_config, config)
            config = merged_config
        
        # Determine which analyses to run
        analyses_to_run = _determine_analyses(analysis, config, registry)
        
        # Determine output format
        output_format = _determine_format(format, config, registry)
        
        # Extract circuit data for simulation
        circuit_data = _extract_circuit_data(circuit)
        
        # Run all requested analyses
        analysis_results = {}
        
        for analysis_name in analyses_to_run:
            logger.info(f"Running {analysis_name} analysis...")
            
            try:
                # Get analysis plugin
                plugin_class = registry.get_analysis_plugin(analysis_name)
                if not plugin_class:
                    raise ValueError(f"Analysis plugin '{analysis_name}' not found")
                
                plugin = plugin_class()
                
                # Prepare analysis
                prepared_params = plugin.prepare_analysis(circuit_data, config)
                
                # Execute analysis
                results = plugin.execute_analysis(prepared_params)
                analysis_results[analysis_name] = results
                
                logger.info(f"✅ {analysis_name} analysis completed")
                
            except Exception as e:
                logger.error(f"❌ {analysis_name} analysis failed: {e}")
                # Continue with other analyses, but mark this one as failed
                analysis_results[analysis_name] = {"error": str(e), "status": "failed"}
        
        # Generate report
        logger.info(f"Generating {output_format} report...")
        
        format_plugin_class = registry.get_format_plugin(output_format)
        if not format_plugin_class:
            raise ValueError(f"Format plugin '{output_format}' not found")
        
        format_plugin = format_plugin_class()
        report_path = format_plugin.generate_report(circuit_data, analysis_results, config)
        
        logger.info(f"✅ Simulation completed successfully")
        logger.info(f"📄 Report saved: {report_path}")
        
        return report_path
        
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        raise


def _determine_analyses(analysis: Optional[Union[str, List[str]]], 
                       config: Dict[str, Any], 
                       registry) -> List[str]:
    """Determine which analysis types to run."""
    
    if analysis is None:
        # Use default from config
        default_analyses = config.get('analysis', {}).get('default_types', ['dc', 'ac', 'transient'])
        return [a for a in default_analyses if config.get('analysis', {}).get(a, {}).get('enabled', True)]
    
    elif isinstance(analysis, str):
        return [analysis]
    
    elif isinstance(analysis, list):
        return analysis
    
    else:
        raise ValueError(f"Invalid analysis parameter type: {type(analysis)}")


def _determine_format(format_param: str, config: Dict[str, Any], registry) -> str:
    """Determine output format to use."""
    
    if format_param == "default":
        return config.get('output', {}).get('default_format', 'html')
    
    return format_param


def _extract_circuit_data(circuit) -> Dict[str, Any]:
    """Extract circuit data in format suitable for simulation."""
    
    try:
        # Try to use existing JSON export functionality with proper encoder
        import tempfile
        import json
        from ..core.json_encoder import CircuitSynthJSONEncoder
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Generate JSON netlist using custom encoder
            circuit_data = {
                'name': circuit.name,
                'description': getattr(circuit, 'description', ''),
                'components': {},
                'nets': {}
            }
            
            # Extract components first
            for i, component in enumerate(circuit.components):
                comp_data = {
                    'ref': getattr(component, 'ref', f'U{i+1}'),
                    'symbol': getattr(component, 'symbol', 'Device:R'),
                    'value': getattr(component, 'value', '1k'),
                    'footprint': getattr(component, 'footprint', 'Resistor_SMD:R_0603_1608Metric')
                }
                circuit_data['components'][comp_data['ref']] = comp_data
            
            # Extract nets in the format expected by circuit-simulation
            # nets should be: {"net_name": [{"component": "ref", "pin": {"number": "1", "name": "~", "type": "passive"}}]}
            for net_name, net in circuit.nets.items():
                circuit_data['nets'][net_name] = []
            
            # Build net connections by looking at component pins
            for i, component in enumerate(circuit.components):
                comp_ref = getattr(component, 'ref', f'U{i+1}')
                if hasattr(component, 'pins'):
                    for pin_num, net in getattr(component, 'pins', {}).items():
                        if net:
                            net_name = str(net.name) if hasattr(net, 'name') else str(net)
                            if net_name in circuit_data['nets']:
                                connection = {
                                    "component": comp_ref,
                                    "pin": {
                                        "number": str(pin_num),
                                        "name": "~",
                                        "type": "passive"
                                    }
                                }
                                circuit_data['nets'][net_name].append(connection)
            
            # Write with custom encoder
            with open(temp_path, 'w') as f:
                json.dump(circuit_data, f, cls=CircuitSynthJSONEncoder, indent=2)
            
            # Read back the data
            with open(temp_path, 'r') as f:
                circuit_data = json.load(f)
            
            return circuit_data
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Failed to extract circuit data: {e}")
        
        # Fallback: create minimal circuit data directly
        try:
            circuit_data = {
                'name': circuit.name,
                'description': getattr(circuit, 'description', ''),
                'components': {},
                'nets': {}
            }
            
            # Simple component extraction
            for i, component in enumerate(circuit.components):
                ref = getattr(component, 'ref', f'U{i+1}')
                circuit_data['components'][ref] = {
                    'ref': ref,
                    'symbol': getattr(component, 'symbol', 'Device:R'),
                    'value': getattr(component, 'value', '1k'),
                    'footprint': getattr(component, 'footprint', 'Resistor_SMD:R_0603_1608Metric')
                }
            
            # Simple net extraction - in correct format for circuit-simulation
            for net_name in circuit.nets.keys():
                circuit_data['nets'][net_name] = []  # List format expected
            
            # Build connections 
            for i, component in enumerate(circuit.components):
                comp_ref = getattr(component, 'ref', f'U{i+1}')
                if hasattr(component, 'pins'):
                    for pin_num, net in getattr(component, 'pins', {}).items():
                        if net:
                            net_name = str(net.name) if hasattr(net, 'name') else str(net)
                            if net_name in circuit_data['nets']:
                                connection = {
                                    "component": comp_ref,
                                    "pin": {
                                        "number": str(pin_num),
                                        "name": "~", 
                                        "type": "passive"
                                    }
                                }
                                circuit_data['nets'][net_name].append(connection)
            
            return circuit_data
            
        except Exception as fallback_error:
            logger.error(f"Fallback extraction also failed: {fallback_error}")
            return {
                'name': getattr(circuit, 'name', 'unknown_circuit'),
                'components': {},
                'nets': {},
                'error': f"Failed to extract circuit data: {e}"
            }


def _deep_merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries."""
    
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


# Convenience functions for specific analysis types
def simulate_dc(circuit, config: Optional[Dict[str, Any]] = None, format: str = "default") -> str:
    """Run DC analysis only."""
    return simulate(circuit, analysis="dc", config=config, format=format)


def simulate_ac(circuit, config: Optional[Dict[str, Any]] = None, format: str = "default") -> str:
    """Run AC analysis only."""
    return simulate(circuit, analysis="ac", config=config, format=format)


def simulate_transient(circuit, config: Optional[Dict[str, Any]] = None, format: str = "default") -> str:
    """Run transient analysis only."""
    return simulate(circuit, analysis="transient", config=config, format=format)


def simulate_all(circuit, config: Optional[Dict[str, Any]] = None, format: str = "default") -> str:
    """Run all available analysis types."""
    registry = get_plugin_registry()
    all_analyses = registry.list_analysis_plugins()
    return simulate(circuit, analysis=all_analyses, config=config, format=format)


def list_available_analyses() -> List[str]:
    """List all available analysis types."""
    registry = get_plugin_registry()
    return registry.list_analysis_plugins()


def list_available_formats() -> List[str]:
    """List all available output formats."""
    registry = get_plugin_registry()
    return registry.list_format_plugins()


def get_plugin_info() -> Dict[str, Any]:
    """Get detailed information about all available plugins."""
    registry = get_plugin_registry()
    return {
        'analysis_plugins': registry.get_analysis_plugin_info(),
        'format_plugins': registry.get_format_plugin_info()
    }