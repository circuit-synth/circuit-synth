#!/usr/bin/env python3
"""
Claude Code Bridge for KiCad Plugins - FIXED VERSION

This version fixes the EPIPE crash issue by:
1. Using stdin input instead of command arguments
2. Shorter context messages 
3. Better subprocess handling
4. Proper error handling for Node.js CLI issues
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
    
    def to_claude_context(self) -> str:
        """Format circuit data for Claude Code context - SHORTENED VERSION."""
        # Create a much shorter context to avoid EPIPE issues
        context = f"""KiCad Project: {self.project_name}
Components: {len(self.components)}
Nets: {len(self.nets)}

Key Components:"""
        
        # Show only first 5 components to keep message short
        for comp in self.components[:5]:
            ref = comp.get('ref', 'Unknown')
            value = comp.get('value', 'N/A')
            context += f"\n- {ref}: {value}"
        
        if len(self.components) > 5:
            context += f"\n- ... and {len(self.components) - 5} more"
        
        return context


class ClaudeBridge:
    """
    Bridge between KiCad plugins and Claude Code - FIXED VERSION.
    
    Fixes EPIPE crashes and subprocess issues.
    """
    
    def __init__(self):
        self.is_connected = False
        self.session_id = None
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kicad_claude_"))
        self.context_file = self.temp_dir / "circuit_context.md"
        self.conversation_history: List[Dict] = []
        self.claude_path = "/Users/shanemattner/.nvm/versions/node/v23.7.0/bin/claude"
        
        logger.info(f"Claude Bridge initialized with temp dir: {self.temp_dir}")
    
    def connect(self) -> bool:
        """
        Establish connection with Claude Code - FIXED VERSION.
        """
        try:
            # Test connection with minimal command
            result = subprocess.run(
                [self.claude_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10,
                stdin=subprocess.DEVNULL  # Prevent EPIPE
            )
            
            if result.returncode == 0:
                self.is_connected = True
                logger.info("Successfully connected to Claude Code")
                return True
            else:
                logger.warning("Claude Code not found or not responding")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Claude Code: {e}")
            return False
    
    def set_circuit_context(self, circuit_data) -> None:
        """Set the current circuit context."""
        try:
            context_content = circuit_data.to_claude_context()
            self.context_file.write_text(context_content)
            self.current_circuit = circuit_data
            logger.info(f"Circuit context set for {circuit_data.project_name}")
        except Exception as e:
            logger.error(f"Failed to set circuit context: {e}")
    
    def send_message(self, message: str, circuit_data = None) -> str:
        """
        Send message to Claude - FIXED VERSION to prevent EPIPE crashes.
        """
        if not self.is_connected:
            return "❌ Not connected to Claude Code"
        
        try:
            # Update context if provided
            if circuit_data:
                self.set_circuit_context(circuit_data)
            
            # Create a SHORT message to avoid EPIPE issues
            if hasattr(self, 'current_circuit'):
                context = self.current_circuit.to_claude_context()
                # Keep the message much shorter
                full_message = f"""KiCad Circuit Question:

{context}

Q: {message}

Please provide a brief, helpful answer about this KiCad circuit."""
            else:
                full_message = f"KiCad Question: {message}"
            
            # Use the FIXED subprocess call
            response = self._call_claude_cli_fixed(full_message)
            
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
    
    def _call_claude_cli_fixed(self, message: str) -> str:
        """
        FIXED Claude CLI call that prevents EPIPE crashes.
        
        Uses stdin input instead of command arguments to avoid Node.js EPIPE issues.
        """
        try:
            logger.info(f"📤 Sending message to Claude (length: {len(message)})")
            
            # Use Popen with stdin to avoid EPIPE issues
            process = subprocess.Popen(
                [self.claude_path],  # No message argument - use stdin instead
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=dict(os.environ)  # Clean environment
            )
            
            # Send message via stdin and close it properly
            try:
                stdout, stderr = process.communicate(input=message, timeout=45)
                
                if process.returncode == 0:
                    response = stdout.strip()
                    logger.info(f"📥 Got Claude response (length: {len(response)})")
                    return response
                else:
                    error_msg = stderr.strip() if stderr else f"Process failed with code {process.returncode}"
                    logger.error(f"❌ Claude CLI error: {error_msg}")
                    return f"❌ Claude CLI error: {error_msg}"
                    
            except subprocess.TimeoutExpired:
                logger.error("⏰ Claude request timed out, killing process")
                process.kill()
                process.communicate()  # Clean up
                return "❌ Claude request timed out (45 seconds)"
                
        except Exception as e:
            logger.error(f"❌ Failed to call Claude CLI: {e}")
            return f"❌ Failed to call Claude CLI: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def export_conversation(self, file_path: str) -> bool:
        """Export conversation history to a file."""
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


# Simplified data extractor for schematic data
def extract_schematic_data_simple(netlist_path: str):
    """Extract circuit data from KiCad schematic netlist - SIMPLIFIED."""
    circuit_data = CircuitData()
    circuit_data.editor_type = "schematic"
    circuit_data.file_path = netlist_path
    
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(netlist_path)
        root = tree.getroot()
        
        # Extract design name
        design_element = root.find('.//design')
        if design_element is not None:
            source_element = design_element.find('source')
            if source_element is not None:
                circuit_data.project_name = Path(source_element.text).stem
        
        # Extract components (limit to prevent long messages)
        for comp in root.findall('.//components/comp')[:20]:  # Limit to 20 components
            ref = comp.get('ref', 'Unknown')
            value_elem = comp.find('value')
            value = value_elem.text if value_elem is not None else 'N/A'
            
            circuit_data.components.append({
                'ref': ref,
                'value': value
            })
        
        # Extract nets (limit to prevent long messages)
        for net in root.findall('.//nets/net')[:15]:  # Limit to 15 nets
            net_name = net.get('name', 'Unknown')
            nodes = []
            
            for node in net.findall('node'):
                nodes.append({
                    'ref': node.get('ref', 'Unknown'),
                    'pin': node.get('pin', 'Unknown')
                })
            
            circuit_data.nets.append({
                'name': net_name,
                'nodes': nodes
            })
            
    except Exception as e:
        logger.error(f"Error extracting schematic data: {e}")
    
    return circuit_data


# Global bridge instance
_bridge_instance = None

def get_claude_bridge():
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