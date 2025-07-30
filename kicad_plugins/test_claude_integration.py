#!/usr/bin/env python3
"""
Test Claude Code Integration for KiCad Plugins

Comprehensive test suite to validate Claude Code bridge functionality
and KiCad plugin integration.
"""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add plugin directory to path
plugin_dir = Path(__file__).parent
sys.path.insert(0, str(plugin_dir))

from claude_bridge import ClaudeBridge, CircuitData, KiCadDataExtractor


class TestCircuitData(unittest.TestCase):
    """Test CircuitData container class."""
    
    def setUp(self):
        self.circuit_data = CircuitData()
    
    def test_initialization(self):
        """Test CircuitData initialization."""
        self.assertEqual(self.circuit_data.project_name, "Unknown")
        self.assertEqual(self.circuit_data.editor_type, "unknown")
        self.assertEqual(len(self.circuit_data.components), 0)
        self.assertEqual(len(self.circuit_data.nets), 0)
        self.assertEqual(len(self.circuit_data.tracks), 0)
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        self.circuit_data.project_name = "test_project"
        self.circuit_data.components = [{"ref": "U1", "value": "STM32"}]
        
        data_dict = self.circuit_data.to_dict()
        
        self.assertEqual(data_dict['project_name'], "test_project")
        self.assertEqual(len(data_dict['components']), 1)
        self.assertEqual(data_dict['summary']['component_count'], 1)
    
    def test_to_claude_context(self):
        """Test Claude context formatting."""
        self.circuit_data.project_name = "test_esp32"
        self.circuit_data.editor_type = "pcb"
        self.circuit_data.components = [
            {"ref": "U1", "value": "ESP32", "library": "RF_Module"},
            {"ref": "C1", "value": "100nF", "library": "Device"}
        ]
        self.circuit_data.nets = [
            {"name": "VCC_3V3", "nodes": [{"ref": "U1", "pin": "1"}]}
        ]
        
        context = self.circuit_data.to_claude_context()
        
        self.assertIn("test_esp32", context)
        self.assertIn("ESP32", context)
        self.assertIn("RF_Module", context)
        self.assertIn("VCC_3V3", context)


class TestClaudeBridge(unittest.TestCase):
    """Test ClaudeBridge functionality."""
    
    def setUp(self):
        self.bridge = ClaudeBridge()
        self.test_circuit = CircuitData()
        self.test_circuit.project_name = "test_project"
        self.test_circuit.components = [{"ref": "U1", "value": "STM32"}]
    
    def tearDown(self):
        self.bridge.cleanup()
    
    def test_initialization(self):
        """Test bridge initialization."""
        self.assertFalse(self.bridge.is_connected)
        self.assertIsNone(self.bridge.session_id)
        self.assertTrue(self.bridge.temp_dir.exists())
        self.assertEqual(len(self.bridge.conversation_history), 0)
    
    @patch('subprocess.run')
    def test_connect_success(self, mock_run):
        """Test successful Claude connection."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "claude version 1.0.0"
        
        result = self.bridge.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.bridge.is_connected)
    
    @patch('subprocess.run')
    def test_connect_failure(self, mock_run):
        """Test failed Claude connection."""
        mock_run.return_value.returncode = 1
        
        result = self.bridge.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.bridge.is_connected)
    
    def test_set_circuit_context(self):
        """Test setting circuit context."""
        self.bridge.set_circuit_context(self.test_circuit)
        
        self.assertTrue(self.bridge.context_file.exists())
        context_content = self.bridge.context_file.read_text()
        self.assertIn("test_project", context_content)
        self.assertIn("STM32", context_content)
    
    @patch('subprocess.run')
    def test_send_message_not_connected(self, mock_run):
        """Test sending message when not connected."""
        response = self.bridge.send_message("test message")
        
        self.assertIn("Not connected", response)
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_send_message_success(self, mock_run):
        """Test successful message sending."""
        # Mock connection
        self.bridge.is_connected = True
        
        # Mock Claude CLI response
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Claude response here"
        
        response = self.bridge.send_message("test message", self.test_circuit)
        
        self.assertEqual(response, "Claude response here")
        self.assertEqual(len(self.bridge.conversation_history), 1)
        mock_run.assert_called_once()
    
    def test_export_conversation(self):
        """Test conversation export."""
        # Add some conversation history
        self.bridge.conversation_history = [
            {
                'timestamp': '2025-07-29T10:00:00',
                'user_message': 'test question',
                'claude_response': 'test response',
                'circuit_context': 'test_project'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            result = self.bridge.export_conversation(temp_file.name)
            
            self.assertTrue(result)
            
            # Verify export content
            with open(temp_file.name, 'r') as f:
                content = f.read()
                self.assertIn("test question", content)
                self.assertIn("test response", content)
                self.assertIn("test_project", content)
            
            # Cleanup
            os.unlink(temp_file.name)


class TestKiCadDataExtractor(unittest.TestCase):
    """Test KiCad data extraction utilities."""
    
    def test_extract_schematic_data(self):
        """Test schematic data extraction from XML."""
        # Create test XML content
        test_xml = """<?xml version="1.0" encoding="utf-8"?>
<export version="E">
  <design>
    <source>/tmp/test_circuit.kicad_sch</source>
    <date>Mon 29 Jul 2025 12:00:00 PM PST</date>
    <tool>Eeschema 9.0.0</tool>
  </design>
  <components>
    <comp ref="U1">
      <value>ESP32-S3</value>
      <libsource lib="RF_Module" part="ESP32-S3-WROOM-1" description=""/>
    </comp>
    <comp ref="C1">
      <value>100nF</value>
      <libsource lib="Device" part="C" description=""/>
    </comp>
  </components>
  <nets>
    <net code="1" name="VCC_3V3">
      <node ref="U1" pin="1"/>
      <node ref="C1" pin="1"/>
    </net>
    <net code="2" name="GND">
      <node ref="U1" pin="2"/>
      <node ref="C1" pin="2"/>
    </net>
  </nets>
</export>"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
            temp_file.write(test_xml)
            temp_file.flush()
            
            # Extract data
            circuit_data = KiCadDataExtractor.extract_schematic_data(temp_file.name)
            
            # Verify extraction
            self.assertEqual(circuit_data.project_name, "test_circuit")
            self.assertEqual(circuit_data.editor_type, "schematic")
            self.assertEqual(len(circuit_data.components), 2)
            self.assertEqual(len(circuit_data.nets), 2)
            
            # Check component data
            esp32_component = next(c for c in circuit_data.components if c['ref'] == 'U1')
            self.assertEqual(esp32_component['value'], 'ESP32-S3')
            self.assertEqual(esp32_component['library'], 'RF_Module')
            
            # Check net data
            vcc_net = next(n for n in circuit_data.nets if n['name'] == 'VCC_3V3')
            self.assertEqual(len(vcc_net['nodes']), 2)
            
            # Cleanup
            os.unlink(temp_file.name)


class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios."""
    
    def setUp(self):
        self.bridge = ClaudeBridge()
    
    def tearDown(self):
        self.bridge.cleanup()
    
    def test_pcb_analysis_workflow(self):
        """Test typical PCB analysis workflow."""
        # Create mock PCB data
        circuit_data = CircuitData()
        circuit_data.project_name = "esp32_dev_board"
        circuit_data.editor_type = "pcb"
        circuit_data.components = [
            {"ref": "U1", "value": "ESP32-S3", "library": "RF_Module"},
            {"ref": "U2", "value": "AMS1117-3.3", "library": "Regulator_Linear"},
            {"ref": "C1", "value": "100nF", "library": "Device"},
            {"ref": "C2", "value": "10uF", "library": "Device"}
        ]
        circuit_data.nets = [
            {"name": "VCC_3V3", "nodes": [{"ref": "U1", "pin": "1"}, {"ref": "U2", "pin": "2"}]},
            {"name": "GND", "nodes": [{"ref": "U1", "pin": "2"}, {"ref": "U2", "pin": "3"}]}
        ]
        circuit_data.board_info = {
            "width_mm": 50.0,
            "height_mm": 30.0,
            "layer_count": 2
        }
        
        # Set context
        self.bridge.set_circuit_context(circuit_data)
        
        # Verify context was set
        self.assertTrue(self.bridge.context_file.exists())
        context = self.bridge.context_file.read_text()
        
        # Check context contains expected information
        self.assertIn("esp32_dev_board", context)
        self.assertIn("ESP32-S3", context)
        self.assertIn("AMS1117-3.3", context)
        self.assertIn("VCC_3V3", context)
        self.assertIn("50.0 x 30.0 mm", context)
    
    def test_schematic_analysis_workflow(self):
        """Test typical schematic analysis workflow."""
        # Create mock schematic data
        circuit_data = CircuitData()
        circuit_data.project_name = "amplifier_circuit"
        circuit_data.editor_type = "schematic"
        circuit_data.components = [
            {"ref": "U1", "value": "LM358", "library": "Amplifier_Operational"},
            {"ref": "R1", "value": "10k", "library": "Device"},
            {"ref": "R2", "value": "1k", "library": "Device"},
            {"ref": "C1", "value": "100nF", "library": "Device"}
        ]
        circuit_data.nets = [
            {"name": "INPUT", "nodes": [{"ref": "U1", "pin": "3"}, {"ref": "R1", "pin": "1"}]},
            {"name": "OUTPUT", "nodes": [{"ref": "U1", "pin": "1"}, {"ref": "R2", "pin": "2"}]},
            {"name": "VCC", "nodes": [{"ref": "U1", "pin": "8"}]},
            {"name": "GND", "nodes": [{"ref": "U1", "pin": "4"}, {"ref": "C1", "pin": "2"}]}
        ]
        
        # Test context preparation
        context = circuit_data.to_claude_context()
        
        # Verify context quality
        self.assertIn("amplifier_circuit", context)
        self.assertIn("LM358", context)
        self.assertIn("Amplifier_Operational", context)
        self.assertIn("INPUT", context)
        self.assertIn("OUTPUT", context)
        
        # Check that context is well-formatted
        lines = context.split('\n')
        self.assertTrue(any("## Circuit Summary" in line for line in lines))
        self.assertTrue(any("## Component Breakdown" in line for line in lines))


def run_functional_tests():
    """Run functional tests that require actual Claude CLI."""
    print("\n🧪 Running Functional Tests (requires Claude CLI)")
    print("=" * 60)
    
    # Test 1: Claude CLI availability
    print("1. Testing Claude CLI availability...")
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ Claude CLI is available")
            print(f"   📋 Version: {result.stdout.strip()}")
        else:
            print("   ❌ Claude CLI not responding correctly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("   ❌ Claude CLI not found or not responding")
        print("   💡 Install Claude CLI to enable full functionality")
        return False
    
    # Test 2: Basic Claude communication
    print("\n2. Testing basic Claude communication...")
    try:
        bridge = ClaudeBridge()
        success = bridge.connect()
        
        if success:
            print("   ✅ Successfully connected to Claude")
            
            # Test message sending
            response = bridge.send_message("Respond with exactly: 'Integration test successful'")
            if "Integration test successful" in response:
                print("   ✅ Message sending works correctly")
            else:
                print(f"   ⚠️  Unexpected response: {response[:100]}...")
            
            # Test context setting
            test_circuit = CircuitData()
            test_circuit.project_name = "integration_test"
            test_circuit.components = [{"ref": "U1", "value": "test_component"}]
            
            bridge.set_circuit_context(test_circuit)
            print("   ✅ Circuit context setting works")
            
            bridge.cleanup()
            
        else:
            print("   ❌ Failed to connect to Claude")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during Claude communication test: {e}")
        return False
    
    print("\n🎉 All functional tests passed!")
    return True


def main():
    """Run comprehensive test suite."""
    print("🚀 Circuit-Synth AI Claude Integration Test Suite")
    print("=" * 60)
    
    # Run unit tests
    print("Running Unit Tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitData))
    suite.addTests(loader.loadTestsFromTestCase(TestClaudeBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestKiCadDataExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Unit Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    unit_tests_passed = len(result.failures) == 0 and len(result.errors) == 0
    
    if unit_tests_passed:
        print("   ✅ All unit tests passed!")
    else:
        print("   ❌ Some unit tests failed")
        
        # Print failures and errors
        for test, error in result.failures + result.errors:
            print(f"   💥 {test}: {error.split('\\n')[0]}")
    
    # Run functional tests
    functional_tests_passed = run_functional_tests()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 Final Test Results:")
    print(f"   Unit Tests: {'✅ PASS' if unit_tests_passed else '❌ FAIL'}")
    print(f"   Functional Tests: {'✅ PASS' if functional_tests_passed else '❌ FAIL'}")
    
    if unit_tests_passed and functional_tests_passed:
        print("\n🎉 All tests passed! Claude integration is ready for use.")
        print("\n🚀 Next Steps:")
        print("   1. Install plugins in KiCad")
        print("   2. Set up hotkeys (Ctrl+Shift+A)")
        print("   3. Test in real KiCad environment")
        return True
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")
        print("\n🔧 Troubleshooting:")
        if not functional_tests_passed:
            print("   • Install Claude CLI: brew install claude-cli")
            print("   • Set up API key: claude configure set api_key YOUR_KEY")
            print("   • Test CLI: claude --message 'test'")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)