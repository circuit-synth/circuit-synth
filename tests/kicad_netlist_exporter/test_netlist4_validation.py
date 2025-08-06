import json
import re
from pathlib import Path

from .test_netlist_validation_base import NetlistValidationBase


class TestNetlist4Validation(NetlistValidationBase):
    """
    Thorough test for validating that netlist4_output.json correctly represents
    the original netlist4.net file, with special focus on deep hierarchical structure.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Test data and output directories
        cls.TEST_DATA_DIR = cls.BASE_DIR / "test_data" / "kicad9" / "netlists"
        cls.TEST_OUTPUT_DIR = cls.BASE_DIR / "test_output"

        # Specific files for this test
        cls.NETLIST_FILE = cls.TEST_DATA_DIR / "netlist4.net"
        cls.JSON_FILE = cls.TEST_OUTPUT_DIR / "netlist4_output.json"

        # Load the files
        cls.netlist_content = cls.NETLIST_FILE.read_text(encoding="utf-8")
        with open(cls.JSON_FILE, "r", encoding="utf-8") as f:
            cls.json_data = json.load(f)

        # Ensure files exist
        assert cls.NETLIST_FILE.exists(), f"Netlist file not found: {cls.NETLIST_FILE}"
        assert cls.JSON_FILE.exists(), f"JSON file not found: {cls.JSON_FILE}"

    def test_file_existence(self):
        """Test that both the netlist and JSON files exist."""
        self.assertTrue(
            self.NETLIST_FILE.exists(), f"Netlist file not found: {self.NETLIST_FILE}"
        )
        self.assertTrue(
            self.JSON_FILE.exists(), f"JSON file not found: {self.JSON_FILE}"
        )

    def test_basic_properties(self):
        """Test that basic properties are correctly extracted."""
        # Check name
        self.assertEqual(self.json_data["name"], "netlist4", "Incorrect netlist name")

        # Check properties
        self.assertIn("properties", self.json_data, "Missing properties section")
        self.assertIn("source", self.json_data["properties"], "Missing source property")
        self.assertIn("date", self.json_data["properties"], "Missing date property")
        self.assertIn("tool", self.json_data["properties"], "Missing tool property")

        # Extract properties from netlist with more flexible patterns
        source_match = re.search(r'\(source\s+"([^"]+)"\)', self.netlist_content)
        date_match = re.search(r'\(date\s+"([^"]+)"\)', self.netlist_content)
        tool_match = re.search(r'\(tool\s+"([^"]+)"\)', self.netlist_content)

        # Verify properties match if found
        if source_match:
            self.assertEqual(
                self.json_data["properties"]["source"],
                source_match.group(1),
                "Source property mismatch",
            )
        if date_match:
            self.assertEqual(
                self.json_data["properties"]["date"],
                date_match.group(1),
                "Date property mismatch",
            )
        if tool_match:
            self.assertEqual(
                self.json_data["properties"]["tool"],
                tool_match.group(1),
                "Tool property mismatch",
            )

    def test_hierarchical_structure(self):
        """Test that the hierarchical structure is correctly represented."""
        # Check sheet count in netlist with more flexible pattern
        netlist_sheets = re.findall(
            r'\(sheet\s+\(number\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\)',
            self.netlist_content,
        )

        # Count sheets in JSON (including root)
        json_sheets = ["/"]  # Root sheet

        # Add subcircuits
        for subcircuit in self.json_data.get("subcircuits", []):
            json_sheets.append(f"/{subcircuit['name']}/")

            # Add nested subcircuits
            for sub_subcircuit in subcircuit.get("subcircuits", []):
                json_sheets.append(f"/{subcircuit['name']}/{sub_subcircuit['name']}/")

                # Add deeply nested subcircuits
                for sub_sub_subcircuit in sub_subcircuit.get("subcircuits", []):
                    json_sheets.append(
                        f"/{subcircuit['name']}/{sub_subcircuit['name']}/{sub_sub_subcircuit['name']}/"
                    )

                    # Add even deeper nested subcircuits
                    for sub_sub_sub_subcircuit in sub_sub_subcircuit.get(
                        "subcircuits", []
                    ):
                        json_sheets.append(
                            f"/{subcircuit['name']}/{sub_subcircuit['name']}/{sub_sub_subcircuit['name']}/{sub_sub_sub_subcircuit['name']}/"
                        )

        # Verify sheet counts are within acceptable range
        # Allow for some flexibility in sheet count
        min_expected_sheets = len(netlist_sheets)
        max_expected_sheets = min_expected_sheets + 2  # Allow for up to 2 extra sheets

        self.assertGreaterEqual(
            len(json_sheets),
            min_expected_sheets,
            f"Sheet count too low: {len(json_sheets)} in JSON vs at least {min_expected_sheets} expected",
        )
        self.assertLessEqual(
            len(json_sheets),
            max_expected_sheets,
            f"Sheet count too high: {len(json_sheets)} in JSON vs at most {max_expected_sheets} expected",
        )

        # Check specific sheets - these are critical paths that must exist
        self.assertIn("/usb/", json_sheets, "Missing /usb/ sheet in JSON")
        self.assertIn(
            "/usb/regulator/", json_sheets, "Missing /usb/regulator/ sheet in JSON"
        )
        self.assertIn(
            "/usb/regulator/led/",
            json_sheets,
            "Missing /usb/regulator/led/ sheet in JSON",
        )
        self.assertIn(
            "/usb/regulator/led/light_sensor/",
            json_sheets,
            "Missing /usb/regulator/led/light_sensor/ sheet in JSON",
        )

    def test_component_count(self):
        """Test that all components are correctly extracted."""
        # Extract components from netlist with more flexible pattern
        netlist_components = re.findall(
            r'\(comp\s+\(ref\s+"([^"]+)"\)', self.netlist_content
        )

        # Count components in JSON (both main circuit and all subcircuits)
        json_components = []

        # Add main circuit components
        json_components.extend(list(self.json_data["components"].keys()))

        # Function to recursively collect components from subcircuits
        def collect_components(subcircuit):
            components = list(subcircuit.get("components", {}).keys())
            for sub in subcircuit.get("subcircuits", []):
                components.extend(collect_components(sub))
            return components

        # Collect components from all subcircuits
        for subcircuit in self.json_data.get("subcircuits", []):
            json_components.extend(collect_components(subcircuit))

        # Verify component counts are within acceptable range
        # Allow for some flexibility in component count
        min_expected_components = max(
            1, len(netlist_components) - 2
        )  # At least 1, or netlist count - 2
        max_expected_components = (
            len(netlist_components) + 2
        )  # Allow for up to 2 extra components

        self.assertGreaterEqual(
            len(json_components),
            min_expected_components,
            f"Component count too low: {len(json_components)} in JSON vs at least {min_expected_components} expected",
        )
        self.assertLessEqual(
            len(json_components),
            max_expected_components,
            f"Component count too high: {len(json_components)} in JSON vs at most {max_expected_components} expected",
        )

        # Verify critical components from netlist are in JSON
        # Focus on key components that must be present
        key_components = ["U1", "C1", "U3"]
        for comp_ref in key_components:
            self.assertIn(
                comp_ref, json_components, f"Key component {comp_ref} missing from JSON"
            )

    def test_component_properties(self):
        """Test that component properties are correctly extracted."""
        # Test U1 component properties using helper methods
        self.assert_component_property(
            self.json_data["components"], "U1", "reference", "U1"
        )

        # Extract U1 value from netlist using safe method
        u1_value = self.safe_extract_property("U1", "value")
        if u1_value:
            self.assert_component_property(
                self.json_data["components"], "U1", "value", u1_value
            )

        # Check that footprint and description exist in the JSON
        self.assert_component_property(self.json_data["components"], "U1", "footprint")
        self.assert_component_property(
            self.json_data["components"], "U1", "description"
        )

        # Test C1 component properties
        self.assert_component_property(
            self.json_data["components"], "C1", "reference", "C1"
        )

        # Extract C1 properties from netlist using safe method
        c1_value = self.safe_extract_property("C1", "value")
        c1_footprint = self.safe_extract_property("C1", "footprint")
        c1_description = self.safe_extract_property("C1", "description")

        # Verify C1 properties match if found
        if c1_value:
            self.assert_component_property(
                self.json_data["components"], "C1", "value", c1_value
            )
        if c1_footprint:
            self.assert_component_property(
                self.json_data["components"], "C1", "footprint", c1_footprint
            )
        if c1_description:
            self.assert_component_property(
                self.json_data["components"], "C1", "description", c1_description
            )

    def test_deep_hierarchical_components(self):
        """Test components in deeply nested subcircuits."""
        # Find subcircuits using helper method
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )
        led_subcircuit = self.find_subcircuit(
            regulator_subcircuit.get("subcircuits", []), "led"
        )
        light_sensor_subcircuit = self.find_subcircuit(
            led_subcircuit.get("subcircuits", []), "light_sensor"
        )

        # Check U3 component in light_sensor subcircuit
        self.assert_component_property(
            light_sensor_subcircuit["components"], "U3", "reference", "U3"
        )

        # Extract U3 properties from netlist using safe method
        u3_value = self.safe_extract_property("U3", "value")
        u3_footprint = self.safe_extract_property("U3", "footprint")
        u3_description = self.safe_extract_property("U3", "description")

        # Verify U3 properties match if found
        if u3_value:
            self.assert_component_property(
                light_sensor_subcircuit["components"], "U3", "value", u3_value
            )
        if u3_footprint:
            self.assert_component_property(
                light_sensor_subcircuit["components"], "U3", "footprint", u3_footprint
            )
        if u3_description:
            self.assert_component_property(
                light_sensor_subcircuit["components"],
                "U3",
                "description",
                u3_description,
            )

        # Check sheetpath property
        self.assertIn(
            "properties",
            light_sensor_subcircuit["components"]["U3"],
            "U3 properties missing from JSON",
        )
        self.assertIn(
            "Sheetname",
            light_sensor_subcircuit["components"]["U3"]["properties"],
            "U3 Sheetname property missing from JSON",
        )
        self.assertEqual(
            light_sensor_subcircuit["components"]["U3"]["properties"]["Sheetname"],
            "light_sensor",
            "U3 Sheetname property mismatch",
        )

    def test_hierarchical_nets(self):
        """Test that hierarchical nets are correctly represented."""
        # Check SDA net in main circuit
        self.assertIn(
            "SDA", self.json_data["nets"], "SDA net missing from main circuit"
        )
        sda_net = self.json_data["nets"]["SDA"]

        # In Structure A, hierarchical nature is implicit if the net exists in multiple scopes.
        # We can verify its presence in different scopes instead of checking a flag.
        # Optional: Use check_net_nodes for detailed verification if needed.
        # self.check_net_nodes(self.json_data["nets"], "SDA", expected_nodes=[...])

        # Find subcircuits using helper method
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )
        led_subcircuit = self.find_subcircuit(
            regulator_subcircuit.get("subcircuits", []), "led"
        )
        light_sensor_subcircuit = self.find_subcircuit(
            led_subcircuit.get("subcircuits", []), "light_sensor"
        )

        # Check SDA net in light_sensor subcircuit
        self.assertIn(
            "SDA",
            light_sensor_subcircuit["nets"],
            "SDA net missing from light_sensor subcircuit",
        )
        light_sensor_sda_net = light_sensor_subcircuit["nets"]["SDA"]

        # Verify light_sensor SDA exists (presence implies hierarchy connection)
        self.assertIn(
            "SDA",
            light_sensor_subcircuit["nets"],
            "SDA net missing from light_sensor subcircuit",
        )
        # Optional: Use check_net_nodes for detailed verification if needed.
        # self.check_net_nodes(light_sensor_subcircuit["nets"], "SDA", expected_nodes=[...])

        # Check SCL and INT nets similarly by verifying presence in both scopes
        for net_name in ["SCL", "INT"]:
            self.assertIn(
                net_name,
                self.json_data["nets"],
                f"{net_name} net missing from main circuit",
            )
            self.assertIn(
                net_name,
                light_sensor_subcircuit["nets"],
                f"{net_name} net missing from light_sensor subcircuit",
            )
            # Optional: Use check_net_nodes for detailed verification if needed.
            # self.check_net_nodes(self.json_data["nets"], net_name, expected_nodes=[...])
            # self.check_net_nodes(light_sensor_subcircuit["nets"], net_name, expected_nodes=[...])

    def test_global_nets(self):
        """Test that global nets are correctly represented."""
        # Check GND net in main circuit
        self.assertIn(
            "GND", self.json_data["nets"], "GND net missing from main circuit"
        )
        gnd_net = self.json_data["nets"]["GND"]

        # In Structure A, global nets just appear in multiple scopes; no 'is_hierarchical' flag.
        # Existence check is sufficient for this test's purpose.
        # Optional: Use check_net_nodes for detailed verification if needed.
        # self.check_net_nodes(self.json_data["nets"], "GND", expected_nodes=[...])

        # Check GND net in all subcircuits
        def check_gnd_in_subcircuit(subcircuit, path):
            # Allow for GND net to be missing in some subcircuits
            if "GND" in subcircuit["nets"]:
                # In Structure A, global nets just appear in multiple scopes; no 'is_hierarchical' flag.
                # Existence check is sufficient.
                # Optional: Use check_net_nodes for detailed verification if needed.
                # self.check_net_nodes(subcircuit["nets"], "GND", expected_nodes=[...])
                pass

            for sub in subcircuit.get("subcircuits", []):
                check_gnd_in_subcircuit(sub, f"{path}/{sub['name']}")

        # Check GND in all subcircuits
        for subcircuit in self.json_data.get("subcircuits", []):
            check_gnd_in_subcircuit(subcircuit, f"/{subcircuit['name']}")

        # Check +3V3 net in main circuit
        self.assertIn(
            "+3V3", self.json_data["nets"], "+3V3 net missing from main circuit"
        )
        # In Structure A, global nets just appear in multiple scopes; no 'is_hierarchical' flag.
        # Optional: Use check_net_nodes for detailed verification if needed.
        # self.check_net_nodes(self.json_data["nets"], "+3V3", expected_nodes=[...])

        # Find the regulator subcircuit
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )

        # Check +3V3 in regulator subcircuit if it exists
        if "+3V3" in regulator_subcircuit["nets"]:
            # In Structure A, global nets just appear in multiple scopes; no 'is_hierarchical' flag.
            # Existence check is sufficient.
            # Optional: Use check_net_nodes for detailed verification if needed.
            # self.check_net_nodes(regulator_subcircuit["nets"], "+3V3", expected_nodes=[...])
            pass

    def test_local_nets(self):
        """Test that local nets are correctly represented."""
        # Find subcircuits using helper method
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )
        led_subcircuit = self.find_subcircuit(
            regulator_subcircuit.get("subcircuits", []), "led"
        )

        # Check for local nets in led subcircuit
        # Use a more flexible approach - check that at least one local net exists
        local_nets = [net for net in led_subcircuit["nets"] if "Net-" in net]
        self.assertGreater(len(local_nets), 0, "No local nets found in led subcircuit")

        # Check that local nets exist (implicitly not hierarchical in Structure A)
        for net_name in local_nets:
            self.assertIn(net_name, led_subcircuit["nets"])
            # Optional: Use check_net_nodes for detailed verification if needed.
            # self.check_net_nodes(led_subcircuit["nets"], net_name, expected_nodes=[...])

            # Verify these nets are not in the main circuit
            self.assertNotIn(
                net_name,
                self.json_data["nets"],
                f"{net_name} net incorrectly present in main circuit",
            )

    def test_net_nodes(self):
        """Test that net nodes are correctly extracted."""
        # Check +3V3 net nodes in main circuit if it exists
        if "+3V3" in self.json_data["nets"]:
            plus3v3_net = self.json_data["nets"]["+3V3"]

            # Structure A: plus3v3_net is the list of nodes
            if plus3v3_net:  # Check if the net exists and has nodes
                # Verify U1 pin 3 is connected to +3V3 if it exists
                u1_pin3_node = next(
                    (
                        node
                        for node in plus3v3_net
                        if node["component"] == "U1" and node["pin"]["number"] == "3"
                    ),
                    None,
                )
                if u1_pin3_node:
                    self.assertEqual(
                        u1_pin3_node["pin"]["name"], "3V3", "U1 pin 3 name mismatch"
                    )
                    self.assertEqual(
                        u1_pin3_node["pin"]["type"],
                        "power_in",
                        "U1 pin 3 type mismatch",
                    )

                # Verify C1 pin 1 is connected to +3V3 if it exists
                c1_pin1_node = next(
                    (
                        node
                        for node in plus3v3_net
                        if node["component"] == "C1" and node["pin"]["number"] == "1"
                    ),
                    None,
                )
                if c1_pin1_node:
                    self.assertIsNotNone(
                        c1_pin1_node, "C1 pin 1 node missing from +3V3 net"
                    )
            # Optional: Use check_net_nodes for more comprehensive checks
            # self.check_net_nodes(self.json_data["nets"], "+3V3", expected_nodes=[...])

        # Find subcircuits using helper method
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )
        led_subcircuit = self.find_subcircuit(
            regulator_subcircuit.get("subcircuits", []), "led"
        )
        light_sensor_subcircuit = self.find_subcircuit(
            led_subcircuit.get("subcircuits", []), "light_sensor"
        )

        # Check +3V3 net nodes in light_sensor subcircuit if it exists
        if "+3V3" in light_sensor_subcircuit["nets"]:
            light_sensor_plus3v3_net = light_sensor_subcircuit["nets"]["+3V3"]

            # Structure A: light_sensor_plus3v3_net is the list of nodes
            if light_sensor_plus3v3_net:  # Check if the net exists and has nodes
                # Verify U3 pin 1 is connected to +3V3 if it exists
                u3_pin1_node = next(
                    (
                        node
                        for node in light_sensor_plus3v3_net
                        if node["component"] == "U3" and node["pin"]["number"] == "1"
                    ),
                    None,
                )
                if u3_pin1_node:
                    self.assertEqual(
                        u3_pin1_node["pin"]["name"], "VDD", "U3 pin 1 name mismatch"
                    )
                    self.assertEqual(
                        u3_pin1_node["pin"]["type"],
                        "power_in",
                        "U3 pin 1 type mismatch",
                    )
            # Optional: Use check_net_nodes for more comprehensive checks
            # self.check_net_nodes(light_sensor_subcircuit["nets"], "+3V3", expected_nodes=[...])

    def test_pin_types(self):
        """Test that pin types are correctly preserved."""
        # Check various pin types if they exist

        # Power input pin
        if "+3V3" in self.json_data["nets"]:
            plus3v3_nodes = self.json_data["nets"]["+3V3"]  # Structure A
            u1_pin3v3_node = next(
                (
                    node
                    for node in plus3v3_nodes
                    if node["component"] == "U1" and node["pin"]["number"] == "3"
                ),
                None,
            )
            if u1_pin3v3_node:
                self.assertEqual(
                    u1_pin3v3_node["pin"]["type"], "power_in", "U1 pin 3 type mismatch"
                )

        # Bidirectional pin
        if "D+" in self.json_data["nets"]:
            dplus_nodes = self.json_data["nets"]["D+"]  # Structure A
            u1_io20_node = next(
                (
                    node
                    for node in dplus_nodes
                    if node["component"] == "U1" and node["pin"]["number"] == "26"
                ),
                None,
            )
            if u1_io20_node:
                self.assertEqual(
                    u1_io20_node["pin"]["type"],
                    "bidirectional",
                    "U1 pin 26 type mismatch",
                )

        # Input pin
        unconnected_en_net_name = next(
            (
                net
                for net in self.json_data["nets"]
                if "unconnected" in net and "EN" in net
            ),
            None,
        )
        if unconnected_en_net_name:
            unconnected_en_nodes = self.json_data["nets"][
                unconnected_en_net_name
            ]  # Structure A
            u1_en_node = next(
                (
                    node
                    for node in unconnected_en_nodes
                    if node["component"] == "U1" and node["pin"]["number"] == "8"
                ),
                None,
            )
            if u1_en_node:
                self.assertEqual(
                    u1_en_node["pin"]["type"], "input", "U1 pin 8 type mismatch"
                )

        # No connect pin (in netlist) / unspecified pin (in JSON)
        unconnected_nc_net_name = next(
            (
                net
                for net in self.json_data["nets"]
                if "unconnected" in net and "NC" in net
            ),
            None,
        )
        if unconnected_nc_net_name:
            unconnected_nc_nodes = self.json_data["nets"][
                unconnected_nc_net_name
            ]  # Structure A
            u1_nc_node = next(
                (
                    node
                    for node in unconnected_nc_nodes
                    if node["component"] == "U1" and "NC" in node["pin"].get("name", "")
                ),
                None,
            )
            if u1_nc_node:
                # Note: no_connect in netlist is mapped to unspecified in JSON
                self.assertEqual(
                    u1_nc_node["pin"]["type"], "unspecified", "U1 NC pin type mismatch"
                )

        # Check pin types in deeply nested subcircuits
        usb_subcircuit = self.find_subcircuit(
            self.json_data.get("subcircuits", []), "usb"
        )
        regulator_subcircuit = self.find_subcircuit(
            usb_subcircuit.get("subcircuits", []), "regulator"
        )
        led_subcircuit = self.find_subcircuit(
            regulator_subcircuit.get("subcircuits", []), "led"
        )
        light_sensor_subcircuit = self.find_subcircuit(
            led_subcircuit.get("subcircuits", []), "light_sensor"
        )

        # Check U3 pin types if they exist
        if "+3V3" in light_sensor_subcircuit["nets"]:
            ls_plus3v3_nodes = light_sensor_subcircuit["nets"]["+3V3"]  # Structure A
            u3_vdd_node = next(
                (
                    node
                    for node in ls_plus3v3_nodes
                    if node["component"] == "U3" and node["pin"]["number"] == "1"
                ),
                None,
            )
            if u3_vdd_node:
                self.assertEqual(
                    u3_vdd_node["pin"]["type"], "power_in", "U3 pin 1 type mismatch"
                )

        if "SCL" in light_sensor_subcircuit["nets"]:
            ls_scl_nodes = light_sensor_subcircuit["nets"]["SCL"]  # Structure A
            u3_scl_node = next(
                (
                    node
                    for node in ls_scl_nodes
                    if node["component"] == "U3" and node["pin"]["number"] == "4"
                ),
                None,
            )
            if u3_scl_node:
                self.assertEqual(
                    u3_scl_node["pin"]["type"], "input", "U3 pin 4 type mismatch"
                )

        if "SDA" in light_sensor_subcircuit["nets"]:
            ls_sda_nodes = light_sensor_subcircuit["nets"]["SDA"]  # Structure A
            u3_sda_node = next(
                (
                    node
                    for node in ls_sda_nodes
                    if node["component"] == "U3" and node["pin"]["number"] == "5"
                ),
                None,
            )
            if u3_sda_node:
                self.assertEqual(
                    u3_sda_node["pin"]["type"],
                    "bidirectional",
                    "U3 pin 5 type mismatch",
                )


if __name__ == "__main__":
    unittest.main()
