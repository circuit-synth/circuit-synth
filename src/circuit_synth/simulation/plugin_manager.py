"""
Plugin Manager for Circuit-Synth Simulation System

This module provides an extensible plugin architecture for simulation analysis types
and report formats. Plugins are dynamically discovered and loaded at runtime.

Design Principles:
- No hard-coding: All functionality through discoverable plugins
- Configuration-driven: Plugin behavior controlled via YAML config files
- Interface-based: Abstract interfaces enable custom implementations
- Registry pattern: Dynamic loading and discovery at runtime
"""

import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
import yaml

logger = logging.getLogger(__name__)


class PluginInterface(ABC):
    """Base interface for all simulation plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin-specific configuration."""
        pass


class AnalysisPlugin(PluginInterface):
    """Interface for simulation analysis plugins (DC, AC, Transient, etc.)."""
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration parameters for this analysis type."""
        pass
    
    @abstractmethod
    def prepare_analysis(self, circuit_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare analysis parameters from circuit data and user config."""
        pass
    
    @abstractmethod
    def execute_analysis(self, prepared_params: Dict[str, Any]) -> Any:
        """Execute the analysis and return raw results."""
        pass


class FormatPlugin(PluginInterface):
    """Interface for output format plugins (HTML, PDF, JSON, etc.)."""
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format (e.g., 'html', 'pdf')."""
        pass
    
    @abstractmethod
    def generate_report(self, 
                       circuit_data: Dict[str, Any],
                       analysis_results: Dict[str, Any], 
                       config: Dict[str, Any]) -> str:
        """Generate report and return output file path."""
        pass


class PluginRegistry:
    """Registry for managing plugin discovery and loading."""
    
    def __init__(self):
        self._analysis_plugins: Dict[str, Type[AnalysisPlugin]] = {}
        self._format_plugins: Dict[str, Type[FormatPlugin]] = {}
        self._loaded = False
    
    def discover_plugins(self, plugin_paths: Optional[List[str]] = None) -> None:
        """Discover and register all available plugins."""
        if self._loaded:
            return
            
        # Default plugin search paths
        if plugin_paths is None:
            plugin_paths = [
                "circuit_synth.simulation.plugins.analysis",
                "circuit_synth.simulation.plugins.formats"
            ]
        
        for plugin_path in plugin_paths:
            try:
                self._discover_plugins_in_package(plugin_path)
            except ImportError as e:
                logger.debug(f"Plugin package not found: {plugin_path} - {e}")
                continue
        
        # Discover plugins from external packages
        self._discover_external_plugins()
        
        self._loaded = True
        logger.info(f"Discovered {len(self._analysis_plugins)} analysis plugins, "
                   f"{len(self._format_plugins)} format plugins")
    
    def _discover_plugins_in_package(self, package_name: str) -> None:
        """Discover plugins within a specific package."""
        try:
            package = importlib.import_module(package_name)
            
            if hasattr(package, '__path__'):
                for finder, module_name, ispkg in pkgutil.iter_modules(package.__path__):
                    full_module_name = f"{package_name}.{module_name}"
                    try:
                        module = importlib.import_module(full_module_name)
                        self._register_plugins_from_module(module)
                    except Exception as e:
                        logger.warning(f"Failed to load plugin module {full_module_name}: {e}")
        except ImportError:
            logger.debug(f"Plugin package not found: {package_name}")
    
    def _discover_external_plugins(self) -> None:
        """Discover plugins from external packages using entry points."""
        try:
            # Try to use importlib.metadata (Python 3.8+)
            try:
                from importlib.metadata import entry_points
            except ImportError:
                # Fallback to importlib_metadata for older Python versions
                from importlib_metadata import entry_points
                
            # Look for plugins registered via entry points
            for entry_point in entry_points(group='circuit_synth.simulation.plugins'):
                try:
                    plugin_class = entry_point.load()
                    self._register_plugin_class(plugin_class)
                except Exception as e:
                    logger.warning(f"Failed to load external plugin {entry_point.name}: {e}")
                    
        except ImportError:
            logger.debug("Entry points not available for external plugin discovery")
    
    def _register_plugins_from_module(self, module) -> None:
        """Register all plugin classes found in a module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, PluginInterface):
                # Skip abstract base classes
                if attr is not PluginInterface and attr is not AnalysisPlugin and attr is not FormatPlugin:
                    self._register_plugin_class(attr)
    
    def _register_plugin_class(self, plugin_class: Type[PluginInterface]) -> None:
        """Register a single plugin class."""
        try:
            # Instantiate to get plugin metadata
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.name
            
            if isinstance(plugin_instance, AnalysisPlugin):
                if plugin_name in self._analysis_plugins:
                    logger.warning(f"Analysis plugin '{plugin_name}' already registered, skipping")
                    return
                self._analysis_plugins[plugin_name] = plugin_class
                logger.debug(f"Registered analysis plugin: {plugin_name}")
                
            elif isinstance(plugin_instance, FormatPlugin):
                if plugin_name in self._format_plugins:
                    logger.warning(f"Format plugin '{plugin_name}' already registered, skipping")
                    return
                self._format_plugins[plugin_name] = plugin_class
                logger.debug(f"Registered format plugin: {plugin_name}")
                
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_class}: {e}")
    
    def get_analysis_plugin(self, name: str) -> Optional[Type[AnalysisPlugin]]:
        """Get analysis plugin class by name."""
        return self._analysis_plugins.get(name)
    
    def get_format_plugin(self, name: str) -> Optional[Type[FormatPlugin]]:
        """Get format plugin class by name.""" 
        return self._format_plugins.get(name)
    
    def list_analysis_plugins(self) -> List[str]:
        """Get list of available analysis plugin names."""
        return list(self._analysis_plugins.keys())
    
    def list_format_plugins(self) -> List[str]:
        """Get list of available format plugin names."""
        return list(self._format_plugins.keys())
    
    def get_analysis_plugin_info(self) -> Dict[str, Dict[str, str]]:
        """Get detailed info about all analysis plugins."""
        info = {}
        for name, plugin_class in self._analysis_plugins.items():
            try:
                plugin_instance = plugin_class()
                info[name] = {
                    'version': plugin_instance.version,
                    'class': plugin_class.__name__,
                    'module': plugin_class.__module__
                }
            except Exception as e:
                info[name] = {'error': str(e)}
        return info
    
    def get_format_plugin_info(self) -> Dict[str, Dict[str, str]]:
        """Get detailed info about all format plugins."""
        info = {}
        for name, plugin_class in self._format_plugins.items():
            try:
                plugin_instance = plugin_class()
                info[name] = {
                    'version': plugin_instance.version,
                    'file_extension': plugin_instance.file_extension,
                    'class': plugin_class.__name__,
                    'module': plugin_class.__module__
                }
            except Exception as e:
                info[name] = {'error': str(e)}
        return info


class ConfigurationManager:
    """Manager for loading and validating plugin configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".circuit_synth" / "simulation"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self, config_name: str = "simulation_config.yaml") -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            logger.info(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate configuration
            self._validate_config(config)
            self._configs[config_name] = config
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config {config_path}: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any], config_name: str = "simulation_config.yaml") -> None:
        """Save configuration to YAML file."""
        config_path = self.config_dir / config_name
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logger.info(f"Config saved to: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config {config_path}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'analysis': {
                'default_types': ['dc', 'ac', 'transient'],
                'dc': {
                    'enabled': True
                },
                'ac': {
                    'enabled': True,
                    'start_frequency': '1Hz',
                    'stop_frequency': '1MHz',
                    'points_per_decade': 10,
                    'variation': 'dec'
                },
                'transient': {
                    'enabled': True,
                    'duration': '10ms',
                    'timestep': '1us'
                }
            },
            'output': {
                'default_format': 'html',
                'output_directory': 'simulation_reports',
                'html': {
                    'include_interactive_plots': True,
                    'theme': 'professional'
                }
            },
            'circuit_simulation': {
                'backend_path': '../../../',  # Path to circuit-simulation library
                'timeout': 30  # seconds
            }
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure."""
        required_sections = ['analysis', 'output', 'circuit_simulation']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: {section}")


# Global plugin registry instance
_global_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    if not _global_registry._loaded:
        _global_registry.discover_plugins()
    return _global_registry


def get_configuration_manager() -> ConfigurationManager:
    """Get a configuration manager instance."""
    return ConfigurationManager()