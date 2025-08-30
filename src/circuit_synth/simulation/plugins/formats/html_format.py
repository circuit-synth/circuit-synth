"""
HTML Format Plugin for Circuit-Synth Simulation Reports

This plugin generates professional HTML reports with interactive Plotly charts
using the circuit-simulation library's report generation system.
"""

import logging
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from ...plugin_manager import FormatPlugin

logger = logging.getLogger(__name__)


class HTMLFormatPlugin(FormatPlugin):
    """Plugin for generating interactive HTML reports."""
    
    @property
    def name(self) -> str:
        return "html"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def file_extension(self) -> str:
        return "html"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate HTML format configuration."""
        if not isinstance(config, dict):
            return False
        
        # Check boolean options
        bool_options = ['include_interactive_plots', 'include_summary', 'include_raw_data']
        for option in bool_options:
            if option in config and not isinstance(config[option], bool):
                return False
        
        # Check theme
        if 'theme' in config:
            allowed_themes = ['professional', 'minimal', 'dark', 'light']
            if config['theme'] not in allowed_themes:
                return False
        
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for HTML format."""
        return {
            'include_interactive_plots': True,
            'include_summary': True,
            'include_raw_data': False,
            'theme': 'professional',
            'plot_width': 800,
            'plot_height': 600
        }
    
    def generate_report(self, 
                       circuit_data: Dict[str, Any],
                       analysis_results: Dict[str, Any], 
                       config: Dict[str, Any]) -> str:
        """Generate HTML report and return output file path."""
        
        # Merge default config with user config
        format_config = self.get_default_config()
        format_config.update(config.get('html', {}))
        
        output_config = config.get('output', {})
        backend_config = config.get('circuit_simulation', {})
        
        logger.info("Generating HTML report...")
        
        try:
            # Use circuit-simulation report generation directly
            import sys
            backend_path = Path(backend_config.get('backend_path', '../../../'))
            circuit_sim_path = backend_path / 'src'
            
            if str(circuit_sim_path) not in sys.path:
                sys.path.insert(0, str(circuit_sim_path))
            
            # Determine output directory and filename
            output_dir = Path(output_config.get('output_directory', 'simulation_reports'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            circuit_name = circuit_data.get('name', 'circuit')
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"{circuit_name}_report_{timestamp}.html"
            
            # Try to use the advanced report generation from circuit-simulation
            try:
                from circuit_sim.reports.generator import ReportGenerator
                
                # Create comprehensive report
                generator = ReportGenerator()
                
                # Convert analysis results to the format expected by ReportGenerator
                formatted_results = {}
                for analysis_type, results in analysis_results.items():
                    if results.get('success', True) and 'error' not in results:
                        formatted_results[analysis_type] = results
                
                report_path = generator.generate_report(
                    circuit_name=circuit_name,
                    analysis_results=formatted_results,
                    output_file=str(output_file),
                    include_plots=format_config.get('include_interactive_plots', True),
                    theme=format_config.get('theme', 'professional')
                )
                
                logger.info(f"Professional HTML report generated: {report_path}")
                return str(report_path)
                
            except ImportError:
                logger.debug("Advanced report generator not available, using simple HTML generation")
                # Fall back to simple HTML generation
                return self._generate_simple_html_report(circuit_data, analysis_results, config)
                
        except Exception as e:
            logger.error(f"HTML report generation failed: {e}")
            # Try fallback method
            return self._generate_simple_html_report(circuit_data, analysis_results, config)
    
    def _generate_via_integration(self, circuit_data: Dict[str, Any], analysis_results: Dict[str, Any], 
                                 config: Dict[str, Any], output_file: Path) -> str:
        """Generate report via circuit-simulation integration script."""
        backend_config = config.get('circuit_simulation', {})
        backend_path = Path(backend_config.get('backend_path', '../../../'))
        
        # Use existing advanced_circuit_synth_demo.py as template
        demo_script = backend_path / 'advanced_circuit_synth_demo.py'
        if demo_script.exists():
            logger.debug("Using existing demo script for report generation")
            # This would need to be adapted to work as a library call
            # For now, create a simple HTML report
            
        return self._generate_simple_html_report(circuit_data, analysis_results, config)
    
    def _generate_simple_html_report(self, circuit_data: Dict[str, Any], analysis_results: Dict[str, Any], 
                                   config: Dict[str, Any]) -> str:
        """Generate a simple HTML report as fallback."""
        output_config = config.get('output', {})
        format_config = self.get_default_config()
        format_config.update(config.get('html', {}))
        
        # Determine output directory and filename
        output_dir = Path(output_config.get('output_directory', 'simulation_reports'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        circuit_name = circuit_data.get('name', 'circuit')
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"{circuit_name}_report_{timestamp}.html"
        
        # Generate simple HTML report
        html_content = self._create_simple_html(circuit_data, analysis_results, format_config)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Simple HTML report generated: {output_file}")
        return str(output_file)
    
    def _create_simple_html(self, circuit_data: Dict[str, Any], analysis_results: Dict[str, Any], 
                           format_config: Dict[str, Any]) -> str:
        """Create a simple HTML report."""
        circuit_name = circuit_data.get('name', 'Circuit')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{circuit_name} - Simulation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .analysis-section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .metadata {{ font-size: 0.9em; color: #7f8c8d; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{circuit_name} - Simulation Report</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Circuit:</strong> {circuit_name}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Analysis Types:</strong> {', '.join(analysis_results.keys())}</p>
        </div>"""
        
        # Add analysis results
        for analysis_type, results in analysis_results.items():
            html += f"""
        <div class="analysis-section">
            <h2>{analysis_type.upper()} Analysis Results</h2>
            <pre>{json.dumps(results, indent=2)}</pre>
        </div>"""
        
        # Add circuit data if requested
        if format_config.get('include_raw_data', False):
            html += f"""
        <div class="analysis-section">
            <h2>Circuit Data</h2>
            <pre>{json.dumps(circuit_data, indent=2)}</pre>
        </div>"""
        
        html += f"""
        <div class="metadata">
            <p>Generated by Circuit-Synth HTML Format Plugin v{self.version}</p>
            <p>For interactive plots and advanced features, ensure circuit-simulation backend is properly configured.</p>
        </div>
    </div>
</body>
</html>"""
        
        return html