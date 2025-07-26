import pytest
from circuit_synth.kicad.driver_priority import DriverPriority
from circuit_synth.kicad.net_tracker import NetTracker, NetInfo
from circuit_synth.kicad.net_name_generator import NetNameGenerator

@pytest.fixture
def net_tracker():
    return NetTracker()

@pytest.fixture
def net_name_generator(net_tracker):
    return NetNameGenerator(net_tracker)

class TestDriverPriority:
    def test_priority_ordering(self):
        """Test that priority values are correctly ordered."""
        assert DriverPriority.INVALID < DriverPriority.NONE
        assert DriverPriority.NONE < DriverPriority.PIN
        assert DriverPriority.PIN < DriverPriority.SHEET_PIN
        assert DriverPriority.SHEET_PIN < DriverPriority.HIER_LABEL
        assert DriverPriority.HIER_LABEL < DriverPriority.LOCAL_LABEL
        assert DriverPriority.LOCAL_LABEL < DriverPriority.LOCAL_POWER_PIN
        assert DriverPriority.LOCAL_POWER_PIN < DriverPriority.GLOBAL_POWER_PIN
        assert DriverPriority.GLOBAL_POWER_PIN == DriverPriority.GLOBAL

class TestNetTracker:
    def test_analyze_net_drivers_empty(self, net_tracker):
        """Test analyzing net with no drivers."""
        priority = net_tracker.analyze_net_drivers("net1", [])
        assert priority == DriverPriority.NONE

    def test_analyze_net_drivers_single(self, net_tracker):
        """Test analyzing net with single driver."""
        drivers = [{"type": "local_label", "source": "TEST1"}]
        priority = net_tracker.analyze_net_drivers("net1", drivers)
        assert priority == DriverPriority.LOCAL_LABEL
        
        net_info = net_tracker.get_net_info("net1")
        assert net_info.driver_source == "TEST1"

    def test_analyze_net_drivers_multiple(self, net_tracker):
        """Test analyzing net with multiple drivers of different priorities."""
        drivers = [
            {"type": "pin", "source": "U1_1"},
            {"type": "local_label", "source": "TEST1"},
            {"type": "global", "source": "VCC"}
        ]
        priority = net_tracker.analyze_net_drivers("net1", drivers)
        assert priority == DriverPriority.GLOBAL
        
        net_info = net_tracker.get_net_info("net1")
        assert net_info.driver_source == "VCC"

    def test_track_net_usage(self, net_tracker):
        """Test tracking net usage across sheets."""
        net_tracker.track_net_usage("net1", "/sheet1")
        net_tracker.track_net_usage("net1", "/sheet2")
        
        net_info = net_tracker.get_net_info("net1")
        assert len(net_info.sheet_paths) == 2
        assert "/sheet1" in net_info.sheet_paths
        assert "/sheet2" in net_info.sheet_paths

    def test_hierarchical_net_handling(self, net_tracker):
        """Test handling of hierarchical nets across sheets."""
        # Example from control board: RS485 signals crossing sheets
        net_tracker.track_net_usage("RS485_A", "/Project Architecture")
        net_tracker.track_net_usage("RS485_A", "/Project Architecture/ESP32S3")
        net_tracker.analyze_net_drivers("RS485_A", [{"type": "hier_label", "source": "RS485_A"}])
        
        net_info = net_tracker.get_net_info("RS485_A")
        assert len(net_info.sheet_paths) == 2
        assert net_info.driver_priority == DriverPriority.HIER_LABEL

    def test_power_net_global_handling(self, net_tracker):
        """Test handling of global power nets."""
        # Example from control board: GND net used across multiple sheets
        net_tracker.track_net_usage("GND", "/Project Architecture/ESP32S3")
        net_tracker.track_net_usage("GND", "/Project Architecture/STM32H7")
        net_tracker.track_net_usage("GND", "/Project Architecture/Motor Controller")
        net_tracker.analyze_net_drivers("GND", [{"type": "global_power_pin", "source": "GND"}])
        
        # Add power pins to make it a power net
        power_pins = [
            {"electrical_type": "power_in"},
            {"electrical_type": "power_out"},
            {"electrical_type": "power_in"}
        ]
        net_tracker.detect_power_nets("GND", power_pins)
        
        net_info = net_tracker.get_net_info("GND")
        assert len(net_info.sheet_paths) == 3
        assert net_info.driver_priority == DriverPriority.GLOBAL_POWER_PIN
        assert net_info.is_power_net

    def test_detect_power_nets(self, net_tracker):
        """Test power net detection logic."""
        pins = [
            {"electrical_type": "power_in"},
            {"electrical_type": "power_out"},
            {"electrical_type": "input"}
        ]
        is_power = net_tracker.detect_power_nets("net1", pins)
        assert is_power is True
        
        net_info = net_tracker.get_net_info("net1")
        assert net_info.is_power_net is True

    def test_detect_non_power_nets(self, net_tracker):
        """Test non-power net detection."""
        pins = [
            {"electrical_type": "power_in"},
            {"electrical_type": "input"},
            {"electrical_type": "output"}
        ]
        is_power = net_tracker.detect_power_nets("net1", pins)
        assert is_power is False
        
        net_info = net_tracker.get_net_info("net1")
        assert net_info.is_power_net is False

    def test_net_type_classification(self, net_tracker):
        """Test classification of nets as global/hierarchical/local."""
        # Global power net
        net_tracker.track_net_usage("VDDA", "/Project Architecture/STM32H7")
        net_tracker.analyze_net_drivers("VDDA", [{"type": "global_power_pin", "source": "VDDA"}])
        net_tracker.detect_power_nets("VDDA", [
            {"electrical_type": "power_in"},
            {"electrical_type": "power_out"}
        ])
        assert net_tracker.get_net_info("VDDA").driver_priority == DriverPriority.GLOBAL_POWER_PIN
        assert net_tracker.get_net_info("VDDA").is_power_net

        # Hierarchical signal net
        net_tracker.track_net_usage("RS485_B", "/Project Architecture")
        net_tracker.track_net_usage("RS485_B", "/Project Architecture/ESP32S3")
        net_tracker.analyze_net_drivers("RS485_B", [{"type": "hier_label", "source": "RS485_B"}])
        assert net_tracker.get_net_info("RS485_B").driver_priority == DriverPriority.HIER_LABEL

        # Local net with only pin connections
        net_tracker.track_net_usage("Net-(C15-Pad1)", "/Project Architecture/STM32H7")
        net_tracker.analyze_net_drivers("Net-(C15-Pad1)", [{"type": "pin", "source": "C15_1"}])
        assert net_tracker.get_net_info("Net-(C15-Pad1)").driver_priority == DriverPriority.PIN

class TestNetNameGenerator:
    def test_generate_net_name_unnamed(self, net_name_generator):
        """Test generating name for unknown net."""
        name = net_name_generator.generate_net_name("unknown")
        assert name == "Net-1"

    def test_generate_net_name_with_driver(self, net_tracker, net_name_generator):
        """Test generating name using driver source."""
        drivers = [{"type": "global", "source": "VCC"}]
        net_tracker.analyze_net_drivers("net1", drivers)
        
        name = net_name_generator.generate_net_name("net1")
        assert name == "VCC"

    def test_resolve_bus_names_basic(self, net_tracker, net_name_generator):
        """Test basic bus name resolution with mixed priorities."""
        # Set up some nets with different priorities
        net_tracker.analyze_net_drivers("bus1", [{"type": "hier_label", "source": "BUS[0]"}])
        net_tracker.analyze_net_drivers("bus2", [{"type": "pin", "source": "U1_2"}])
        
        resolved = net_name_generator.resolve_bus_names(
            ["bus1", "bus2", "bus3"],
            "DATA"
        )
        
        assert resolved["bus1"] == "BUS[0]"  # Keeps high priority name
        assert resolved["bus2"] == "DATA[1]"  # Gets position-based name
        assert resolved["bus3"] == "DATA[2]"  # Gets position-based name

    def test_resolve_bus_names_empty_inputs(self, net_tracker, net_name_generator):
        """Test handling of empty inputs."""
        with pytest.raises(ValueError, match="Bus name cannot be empty"):
            net_name_generator.resolve_bus_names(["net1"], "")
            
        with pytest.raises(ValueError, match="Net ID list cannot be empty"):
            net_name_generator.resolve_bus_names([], "BUS")

    def test_resolve_bus_names_duplicate_nets(self, net_tracker, net_name_generator):
        """Test handling of duplicate net IDs."""
        with pytest.raises(ValueError, match="Duplicate net IDs not allowed"):
            net_name_generator.resolve_bus_names(["net1", "net1"], "BUS")

    def test_resolve_bus_names_existing_indices(self, net_tracker, net_name_generator):
        """Test handling of nets with existing indices in their names."""
        # Set up nets with existing indices in names
        net_tracker.analyze_net_drivers("bus1", [{"type": "hier_label", "source": "OLD[5]"}])
        net_tracker.analyze_net_drivers("bus2", [{"type": "local_label", "source": "DATA[3]"}])
        
        resolved = net_name_generator.resolve_bus_names(
            ["bus1", "bus2", "bus3"],
            "NEW"
        )
        
        assert resolved["bus1"] == "OLD[5]"  # Keeps high priority name with index
        assert resolved["bus2"] == "NEW[1]"  # Gets new position-based name (low priority)
        assert resolved["bus3"] == "NEW[2]"  # Gets sequential position-based name

    def test_resolve_bus_names_multiple_buses(self, net_tracker, net_name_generator):
        """Test handling multiple bus groups."""
        # First bus group
        bus1_resolved = net_name_generator.resolve_bus_names(
            ["net1", "net2"],
            "BUS1"
        )
        assert bus1_resolved["net1"] == "BUS1[0]"
        assert bus1_resolved["net2"] == "BUS1[1]"
        
        # Second bus group
        bus2_resolved = net_name_generator.resolve_bus_names(
            ["net3", "net4"],
            "BUS2"
        )
        assert bus2_resolved["net3"] == "BUS2[0]"
        assert bus2_resolved["net4"] == "BUS2[1]"

    def test_resolve_bus_names_malformed_bus_name(self, net_tracker, net_name_generator):
        """Test handling of malformed bus names."""
        # Bus name with existing array notation
        resolved1 = net_name_generator.resolve_bus_names(
            ["net1"],
            "BUS[0]"  # Should be normalized
        )
        assert resolved1["net1"] == "BUS[0]"  # [0] from original name removed, new index added
        
        # Bus name with special characters
        resolved2 = net_name_generator.resolve_bus_names(
            ["net1"],
            "BUS.TEST"  # Special characters allowed in bus name
        )
        assert resolved2["net1"] == "BUS.TEST[0]"

    def test_apply_power_net_rules_global(self, net_tracker, net_name_generator):
        """Test power net naming for global nets."""
        drivers = [{"type": "global_power_pin", "source": "VCC"}]
        net_tracker.analyze_net_drivers("power1", drivers)
        net_tracker.track_net_usage("power1", "/sheet1")
        net_tracker.track_net_usage("power1", "/sheet2")
        net_tracker.detect_power_nets("power1", [
            {"electrical_type": "power_in"},
            {"electrical_type": "power_out"}
        ])
        
        name = net_name_generator.apply_power_net_rules("power1")
        assert name == "VCC"

    def test_apply_power_net_rules_local(self, net_tracker, net_name_generator):
        """Test power net naming for local nets."""
        net_tracker.track_net_usage("power2", "/sheet1")
        net_tracker.detect_power_nets("power2", [
            {"electrical_type": "power_in"},
            {"electrical_type": "power_out"}
        ])
        
        name = net_name_generator.apply_power_net_rules("power2")
        assert name == "LOCAL_PWR-1"