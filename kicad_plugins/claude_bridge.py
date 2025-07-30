#!/usr/bin/env python3
"""
Claude Code Bridge for KiCad Plugins

This module provides a communication bridge between KiCad plugins and Claude Code,
enabling real AI-powered circuit design assistance directly within KiCad.

Features:
- Direct communication with Claude Code session
- Circuit data extraction and formatting for AI analysis
- Real-time AI responses for circuit design questions
- Integration with both PCB and schematic editors
"""

import json
import subprocess
import threading
import queue
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitData:
    """Container for circuit information from KiCad."""
    
    def __init__(self):
        self.project_name: str = "Unknown"
        self.file_path: str = ""
        self.editor_type: str = "unknown"  # "pcb" or "schematic"
        self.components: List[Dict] = []
        self.nets: List[Dict] = []
        self.tracks: List[Dict] = []
        self.board_info: Dict = {}
        self.timestamp: str = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'project_name': self.project_name,
            'file_path': self.file_path,
            'editor_type': self.editor_type,
            'components': self.components,
            'nets': self.nets,
            'tracks': self.tracks,
            'board_info': self.board_info,
            'timestamp': self.timestamp,
            'summary': {
                'component_count': len(self.components),
                'net_count': len(self.nets),
                'track_count': len(self.tracks)
            }
        }
    
    def to_claude_context(self) -> str:
        """Format circuit data for Claude Code context."""
        context = f"""# KiCad Circuit Analysis Context

**Project**: {self.project_name}
**Editor**: {self.editor_type.title()}
**Analysis Time**: {self.timestamp}

## Circuit Summary
- **Components**: {len(self.components)}
- **Nets**: {len(self.nets)}
- **Tracks**: {len(self.tracks)} (PCB only)

## Component Breakdown
"""
        
        # Group components by type/library
        component_types = {}
        for comp in self.components:
            comp_type = comp.get('library', 'Unknown')
            if comp_type not in component_types:
                component_types[comp_type] = []
            component_types[comp_type].append(comp)
        
        for comp_type, comps in sorted(component_types.items()):
            context += f"### {comp_type} ({len(comps)} components)\n"
            for comp in comps[:5]:  # Show first 5
                ref = comp.get('ref', 'Unknown')
                value = comp.get('value', 'N/A')
                context += f"- {ref}: {value}\n"
            if len(comps) > 5:
                context += f"- ... and {len(comps) - 5} more\n"
            context += "\n"
        
        # Add net information if available
        if self.nets:
            context += "## Key Nets\n"
            # Show all nets, prioritizing those with more connections
            sorted_nets = sorted(self.nets, key=lambda n: len(n.get('nodes', [])), reverse=True)[:15]
            for net in sorted_nets:
                net_name = net.get('name', 'Unknown')
                node_count = len(net.get('nodes', []))
                context += f"- {net_name}: {node_count} connections\n"
        
        # Add board information for PCB
        if self.editor_type == "pcb" and self.board_info:
            context += "\n## PCB Information\n"
            for key, value in self.board_info.items():
                context += f"- {key}: {value}\n"
        
        return context


class ClaudeBridge:
    """
    Bridge between KiCad plugins and Claude Code.
    
    Handles communication, context management, and AI response processing.
    """
    
    def __init__(self):
        self.is_connected = False
        self.session_id = None
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kicad_claude_"))
        self.context_file = self.temp_dir / "circuit_context.md"
        self.conversation_history: List[Dict] = []
        self.response_queue = queue.Queue()
        
        logger.info(f"Claude Bridge initialized with temp dir: {self.temp_dir}")
    
    def connect(self) -> bool:
        """
        Establish connection with Claude Code.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test if Claude Code is available
            result = subprocess.run(
                ["claude", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                self.is_connected = True
                logger.info("Successfully connected to Claude Code")
                return True
            else:
                logger.warning("Claude Code not found or not responding")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Failed to connect to Claude Code: {e}")
            return False
    
    def set_circuit_context(self, circuit_data: CircuitData) -> None:
        """
        Set the current circuit context for the AI session.
        
        Args:
            circuit_data: Circuit information from KiCad
        """
        try:
            # Write circuit context to file
            context_content = circuit_data.to_claude_context()
            self.context_file.write_text(context_content)
            
            # Store circuit data for reference
            self.current_circuit = circuit_data
            
            logger.info(f"Circuit context set for {circuit_data.project_name}")
            
        except Exception as e:
            logger.error(f"Failed to set circuit context: {e}")
    
    def send_message(self, message: str, circuit_data: Optional[CircuitData] = None) -> str:
        """
        Send a message to Claude Code and get a response.
        
        Args:
            message: User message to send to Claude
            circuit_data: Optional circuit context to include
            
        Returns:
            str: Claude's response
        """
        if not self.is_connected:
            return "❌ Not connected to Claude Code. Please ensure Claude CLI is installed and available."
        
        try:
            # Update context if provided
            if circuit_data:
                self.set_circuit_context(circuit_data)
            
            # Prepare the full message with context
            full_message = self._prepare_message_with_context(message)
            
            # Send to Claude Code via CLI
            response = self._call_claude_cli(full_message)
            
            # Store in conversation history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user_message': message,
                'claude_response': response,
                'circuit_context': circuit_data.project_name if circuit_data else None
            })
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Error communicating with Claude: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _prepare_message_with_context(self, message: str) -> str:
        """
        Prepare message with circuit context for Claude.
        
        Args:
            message: Original user message
            
        Returns:
            str: Message with circuit context
        """
        if not self.context_file.exists():
            return message
        
        context = self.context_file.read_text()
        
        full_message = f"""I'm working on a KiCad circuit design project and need assistance. Here's the current circuit context:

{context}

**User Question**: {message}

Please provide helpful advice about this circuit design, considering the components, connectivity, and overall design. Focus on practical KiCad workflow suggestions, component recommendations, design optimizations, and any potential issues you can identify.
"""
        
        return full_message
    
    def _call_claude_cli(self, message: str) -> str:
        """
        Call Claude Code CLI with the message.
        
        Args:
            message: Message to send to Claude
            
        Returns:
            str: Claude's response
        """
        try:
            # Call Claude CLI with message as argument
            result = subprocess.run([
                "claude", 
                message
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return f"❌ Claude CLI error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "❌ Claude CLI timeout - request took too long"
        except Exception as e:
            return f"❌ Failed to call Claude CLI: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def export_conversation(self, file_path: str) -> bool:
        """
        Export conversation history to a file.
        
        Args:
            file_path: Path to save the conversation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write("# KiCad-Claude Conversation Export\n\n")
                f.write(f"Export Time: {datetime.now().isoformat()}\n\n")
                
                for entry in self.conversation_history:
                    f.write(f"## [{entry['timestamp']}]\n")
                    if entry.get('circuit_context'):
                        f.write(f"**Circuit**: {entry['circuit_context']}\n\n")
                    f.write(f"**You**: {entry['user_message']}\n\n")
                    f.write(f"**Claude**: {entry['claude_response']}\n\n")
                    f.write("---\n\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            logger.info("Claude Bridge cleaned up successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class KiCadDataExtractor:
    """
    Utility class to extract circuit data from KiCad objects.
    """
    
    @staticmethod
    def extract_pcb_data(board) -> CircuitData:
        """
        Extract circuit data from KiCad PCB board.
        
        Args:
            board: KiCad BOARD object
            
        Returns:
            CircuitData: Extracted circuit information
        """
        circuit_data = CircuitData()
        circuit_data.editor_type = "pcb"
        circuit_data.file_path = board.GetFileName()
        circuit_data.project_name = Path(circuit_data.file_path).stem if circuit_data.file_path else "Unknown"
        
        try:
            # Extract components
            for footprint in board.GetFootprints():
                component = {
                    'ref': footprint.GetReference(),
                    'value': footprint.GetValue(),
                    'library': footprint.GetFPID().GetLibNickname().GetUTF8(),
                    'footprint': footprint.GetFPID().GetLibItemName().GetUTF8(),
                    'position': {
                        'x': float(footprint.GetPosition().x) / 1000000,  # Convert to mm
                        'y': float(footprint.GetPosition().y) / 1000000
                    },
                    'rotation': footprint.GetOrientation().AsDegrees(),
                    'layer': 'Top' if footprint.IsFlipped() else 'Bottom'
                }
                circuit_data.components.append(component)
            
            # Extract tracks
            for track in board.GetTracks():
                track_info = {
                    'start': {
                        'x': float(track.GetStart().x) / 1000000,
                        'y': float(track.GetStart().y) / 1000000
                    },
                    'end': {
                        'x': float(track.GetEnd().x) / 1000000,
                        'y': float(track.GetEnd().y) / 1000000
                    },
                    'width': float(track.GetWidth()) / 1000000,
                    'layer': track.GetLayerName()
                }
                circuit_data.tracks.append(track_info)
            
            # Extract board information
            bbox = board.GetBoundingBox()
            circuit_data.board_info = {
                'width_mm': bbox.GetWidth() / 1000000,
                'height_mm': bbox.GetHeight() / 1000000,
                'layer_count': board.GetCopperLayerCount(),
                'via_count': len([t for t in board.GetTracks() if t.Type() == 1])  # PCB_VIA_T
            }
            
        except Exception as e:
            logger.error(f"Error extracting PCB data: {e}")
        
        return circuit_data
    
    @staticmethod
    def extract_schematic_data(netlist_path: str) -> CircuitData:
        """
        Extract circuit data from KiCad schematic netlist.
        
        Args:
            netlist_path: Path to the netlist XML file
            
        Returns:
            CircuitData: Extracted circuit information
        """
        circuit_data = CircuitData()
        circuit_data.editor_type = "schematic"
        circuit_data.file_path = netlist_path
        
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(netlist_path)
            root = tree.getroot()
            
            # Extract design information
            design_element = root.find('.//design')
            if design_element is not None:
                source_element = design_element.find('source')
                if source_element is not None:
                    source_path = source_element.text
                    circuit_data.project_name = Path(source_path).stem if source_path else Path(netlist_path).stem
                else:
                    circuit_data.project_name = Path(netlist_path).stem
            else:
                circuit_data.project_name = Path(netlist_path).stem
            
            # Extract components
            for comp in root.findall('.//components/comp'):
                ref = comp.get('ref', 'Unknown')
                value_elem = comp.find('value')
                value = value_elem.text if value_elem is not None else 'N/A'
                
                libsource = comp.find('libsource')
                library = libsource.get('lib', 'Unknown') if libsource is not None else 'Unknown'
                part = libsource.get('part', 'Unknown') if libsource is not None else 'Unknown'
                
                component = {
                    'ref': ref,
                    'value': value,
                    'library': library,
                    'part': part
                }
                circuit_data.components.append(component)
            
            # Extract nets
            for net in root.findall('.//nets/net'):
                net_name = net.get('name', 'Unknown')
                nodes = []
                
                for node in net.findall('node'):
                    node_info = {
                        'ref': node.get('ref', 'Unknown'),
                        'pin': node.get('pin', 'Unknown')
                    }
                    nodes.append(node_info)
                
                net_info = {
                    'name': net_name,
                    'nodes': nodes
                }
                circuit_data.nets.append(net_info)
                
        except Exception as e:
            logger.error(f"Error extracting schematic data: {e}")
        
        return circuit_data


# Global bridge instance
_bridge_instance = None

def get_claude_bridge() -> ClaudeBridge:
    """Get the global Claude Bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ClaudeBridge()
    return _bridge_instance


def cleanup_bridge():
    """Clean up the global bridge instance."""
    global _bridge_instance
    if _bridge_instance:
        _bridge_instance.cleanup()
        _bridge_instance = None


# Register cleanup on exit
import atexit
atexit.register(cleanup_bridge)