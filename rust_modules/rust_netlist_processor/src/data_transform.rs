//! Data structures and transformations for netlist processing
//!
//! This module defines the core data structures used throughout the netlist processor,
//! optimized for performance and memory efficiency. All structures support efficient
//! serialization/deserialization and are designed to minimize allocations.

use crate::errors::{NetlistError, Result};
use serde::{Deserialize, Deserializer, Serialize};
use smallvec::SmallVec;
use std::collections::HashMap;
use string_interner::{DefaultSymbol, StringInterner};

/// String interner for memory-efficient string storage
pub type StringPool = StringInterner<DefaultSymbol>;

/// Pin type enumeration matching KiCad's pin types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub enum PinType {
    Input,
    Output,
    Bidirectional,
    PowerIn,
    PowerOut,
    Passive,
    Unspecified,
    NoConnect,
}

impl PinType {
    /// Convert from string representation (case-insensitive)
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "input" => Self::Input,
            "output" => Self::Output,
            "bidirectional" => Self::Bidirectional,
            "power_in" => Self::PowerIn,
            "power_out" => Self::PowerOut,
            "passive" => Self::Passive,
            "no_connect" => Self::NoConnect,
            _ => Self::Unspecified,
        }
    }

    /// Convert to KiCad-compatible string
    pub fn to_kicad_str(self) -> &'static str {
        match self {
            Self::Input => "input",
            Self::Output => "output",
            Self::Bidirectional => "bidirectional",
            Self::PowerIn => "power_in",
            Self::PowerOut => "power_out",
            Self::Passive => "passive",
            Self::NoConnect => "no_connect",
            Self::Unspecified => "passive", // Default to passive for unknown types
        }
    }
}

impl<'de> Deserialize<'de> for PinType {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Ok(PinType::from_str(&s))
    }
}

impl Default for PinType {
    fn default() -> Self {
        Self::Passive
    }
}

/// Pin information with optimized storage
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PinInfo {
    /// Pin number (e.g., "1", "2", "A1")
    pub number: String,
    /// Pin name (e.g., "VCC", "GND", "~")
    pub name: String,
    /// Pin type/function - accepts both "pin_type" and "func" field names
    #[serde(alias = "func")]
    pub pin_type: PinType,
}

impl PinInfo {
    /// Create a new pin with the given information
    pub fn new(number: impl Into<String>, name: impl Into<String>, pin_type: PinType) -> Self {
        Self {
            number: number.into(),
            name: name.into(),
            pin_type,
        }
    }

    /// Create a passive pin (most common case)
    pub fn passive(number: impl Into<String>, name: impl Into<String>) -> Self {
        Self::new(number, name, PinType::Passive)
    }

    /// Check if this is an unconnected pin
    pub fn is_unconnected(&self) -> bool {
        self.pin_type == PinType::NoConnect || self.name.to_uppercase().contains("NC")
    }
}

/// Net node representing a connection point
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NetNode {
    /// Component reference (e.g., "R1", "/MCU/U1")
    pub component: String,
    /// Pin information
    pub pin: PinInfo,
    /// Original hierarchical path (for debugging)
    pub original_path: Option<String>,
}

impl NetNode {
    /// Create a new net node
    pub fn new(component: impl Into<String>, pin: PinInfo) -> Self {
        Self {
            component: component.into(),
            pin,
            original_path: None,
        }
    }

    /// Create a net node with original path tracking
    pub fn with_path(
        component: impl Into<String>,
        pin: PinInfo,
        original_path: impl Into<String>,
    ) -> Self {
        Self {
            component: component.into(),
            pin,
            original_path: Some(original_path.into()),
        }
    }

    /// Get the normalized component reference (without leading slash)
    pub fn normalized_component_ref(&self) -> &str {
        self.component.strip_prefix('/').unwrap_or(&self.component)
    }
}

/// Component representation optimized for netlist generation
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Component {
    /// Component reference designator (e.g., "R1", "U1") - accepts both "reference" and "ref"
    #[serde(alias = "ref")]
    pub reference: String,
    /// Symbol library reference (e.g., "Device:R", "MCU_ST_STM32F4:STM32F407VGTx")
    pub symbol: String,
    /// Component value (e.g., "10k", "STM32F407VG")
    pub value: String,
    /// Footprint reference (e.g., "Resistor_SMD:R_0603_1608Metric")
    pub footprint: String,
    /// Component description
    pub description: String,
    /// Datasheet URL or reference
    pub datasheet: String,
    /// Component properties (key-value pairs)
    pub properties: HashMap<String, String>,
    /// Pin definitions
    pub pins: Vec<PinInfo>,
    /// Component timestamp (UUID)
    #[serde(default = "default_timestamp")]
    pub timestamp: Option<String>,
}

/// Default function for optional timestamp field
fn default_timestamp() -> Option<String> {
    Some(uuid::Uuid::new_v4().to_string())
}

impl Component {
    /// Create a new component with required fields
    pub fn new(
        reference: impl Into<String>,
        symbol: impl Into<String>,
        value: impl Into<String>,
    ) -> Self {
        Self {
            reference: reference.into(),
            symbol: symbol.into(),
            value: value.into(),
            footprint: String::new(),
            description: String::new(),
            datasheet: String::new(),
            properties: HashMap::new(),
            pins: Vec::new(),
            timestamp: Some(uuid::Uuid::new_v4().to_string()),
        }
    }

    /// Get the library name from the symbol
    pub fn library(&self) -> Result<&str> {
        self.symbol.split(':').next().ok_or_else(|| {
            NetlistError::component_error(format!(
                "Invalid symbol format '{}' - expected 'Library:Part'",
                self.symbol
            ))
        })
    }

    /// Get the part name from the symbol
    pub fn part(&self) -> Result<&str> {
        self.symbol.split(':').nth(1).ok_or_else(|| {
            NetlistError::component_error(format!(
                "Invalid symbol format '{}' - expected 'Library:Part'",
                self.symbol
            ))
        })
    }

    /// Add a pin to this component
    pub fn add_pin(&mut self, pin: PinInfo) {
        self.pins.push(pin);
    }

    /// Find a pin by number
    pub fn find_pin(&self, pin_number: &str) -> Option<&PinInfo> {
        self.pins.iter().find(|pin| pin.number == pin_number)
    }

    /// Get all pin numbers
    pub fn pin_numbers(&self) -> Vec<&str> {
        self.pins.iter().map(|pin| pin.number.as_str()).collect()
    }

    /// Check if this component has any unconnected pins
    pub fn has_unconnected_pins(&self) -> bool {
        self.pins.iter().any(|pin| pin.is_unconnected())
    }
}

/// Net representation with hierarchical support
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Net {
    /// Net name (may include hierarchical path)
    #[serde(deserialize_with = "deserialize_net_name")]
    pub name: String,
    /// Connected nodes
    pub nodes: Vec<NetNode>,
    /// Whether this is a hierarchical net
    pub is_hierarchical: bool,
    /// Original net name (before hierarchical processing)
    #[serde(deserialize_with = "deserialize_net_name")]
    pub original_name: String,
    /// Net code (assigned during processing)
    pub code: Option<u32>,
}

/// Custom deserializer for net names that handles null/empty names
fn deserialize_net_name<'de, D>(deserializer: D) -> std::result::Result<String, D::Error>
where
    D: serde::Deserializer<'de>,
{
    use serde::de::Error;

    let opt: Option<String> = Option::deserialize(deserializer)?;
    match opt {
        Some(name) if !name.trim().is_empty() => Ok(name),
        _ => {
            // Return a placeholder that will be replaced during processing
            Ok("__UNNAMED_NET__".to_string())
        }
    }
}

impl Net {
    /// Create a new net
    pub fn new(name: impl Into<String>) -> Self {
        let name = name.into();
        Self {
            original_name: name.clone(),
            name,
            nodes: Vec::new(),
            is_hierarchical: false,
            code: None,
        }
    }

    /// Create a hierarchical net
    pub fn hierarchical(name: impl Into<String>, original_name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            original_name: original_name.into(),
            nodes: Vec::new(),
            is_hierarchical: true,
            code: None,
        }
    }

    /// Add a node to this net
    pub fn add_node(&mut self, node: NetNode) {
        self.nodes.push(node);
    }

    /// Check if this net is empty (no connections)
    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }

    /// Check if this is an unconnected net
    pub fn is_unconnected(&self) -> bool {
        self.name.starts_with("unconnected-") || self.nodes.len() <= 1
    }

    /// Get unique component references connected to this net
    pub fn connected_components(&self) -> Vec<&str> {
        let mut components: Vec<_> = self
            .nodes
            .iter()
            .map(|node| node.normalized_component_ref())
            .collect();
        components.sort_unstable();
        components.dedup();
        components
    }
}

/// Circuit representation with hierarchical support
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Circuit {
    /// Circuit name
    pub name: String,
    /// Circuit description
    pub description: String,
    /// Components in this circuit (keyed by reference)
    pub components: HashMap<String, Component>,
    /// Nets in this circuit (keyed by name)
    pub nets: HashMap<String, Net>,
    /// Subcircuits (hierarchical children)
    pub subcircuits: Vec<Circuit>,
    /// Circuit timestamp/UUID - accepts both "timestamp" and "tstamps"
    #[serde(alias = "tstamps")]
    pub timestamp: String,
    /// Source file information
    pub source_file: String,
}

impl Circuit {
    /// Create a new circuit
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: String::new(),
            components: HashMap::new(),
            nets: HashMap::new(),
            subcircuits: Vec::new(),
            timestamp: uuid::Uuid::new_v4().to_string(),
            source_file: String::new(),
        }
    }

    /// Add a component to this circuit
    pub fn add_component(&mut self, component: Component) {
        self.components
            .insert(component.reference.clone(), component);
    }

    /// Add a net to this circuit
    pub fn add_net(&mut self, net: Net) {
        self.nets.insert(net.name.clone(), net);
    }

    /// Add a subcircuit
    pub fn add_subcircuit(&mut self, subcircuit: Circuit) {
        self.subcircuits.push(subcircuit);
    }

    /// Get all components recursively (including subcircuits)
    pub fn all_components(&self) -> HashMap<String, &Component> {
        let mut all_components = HashMap::new();

        // Add components from this circuit
        for (ref_name, component) in &self.components {
            all_components.insert(ref_name.clone(), component);
        }

        // Add components from subcircuits with hierarchical paths
        for subcircuit in &self.subcircuits {
            let sub_components = subcircuit.all_components();
            for (ref_name, component) in sub_components {
                let hierarchical_ref = if ref_name.starts_with('/') {
                    ref_name
                } else {
                    format!("/{}/{}", subcircuit.name, ref_name)
                };
                all_components.insert(hierarchical_ref, component);
            }
        }

        all_components
    }

    /// Get all nets recursively (including subcircuits)
    pub fn all_nets(&self) -> HashMap<String, &Net> {
        let mut all_nets = HashMap::new();

        // Add nets from this circuit
        for (net_name, net) in &self.nets {
            all_nets.insert(net_name.clone(), net);
        }

        // Add nets from subcircuits
        for subcircuit in &self.subcircuits {
            let sub_nets = subcircuit.all_nets();
            for (net_name, net) in sub_nets {
                all_nets.insert(net_name, net);
            }
        }

        all_nets
    }

    /// Get unique libraries used in this circuit
    pub fn used_libraries(&self) -> Result<Vec<String>> {
        let mut libraries = std::collections::HashSet::new();

        for component in self.all_components().values() {
            libraries.insert(component.library()?.to_string());
        }

        let mut sorted_libs: Vec<_> = libraries.into_iter().collect();
        sorted_libs.sort();
        Ok(sorted_libs)
    }

    /// Parse from JSON data
    pub fn from_json(json_data: &str) -> Result<Self> {
        serde_json::from_str(json_data).map_err(|e| {
            // Include the actual serde error in the message for better debugging
            let detailed_message = format!("Failed to parse circuit JSON data: {}", e);
            NetlistError::json_error(detailed_message, Some(e))
        })
    }

    /// Check if this circuit is effectively empty (no components or nets)
    pub fn is_effectively_empty(&self) -> bool {
        self.components.is_empty()
            && self.nets.is_empty()
            && self.subcircuits.iter().all(|sc| sc.is_effectively_empty())
    }

    /// Convert to JSON string
    pub fn to_json(&self) -> Result<String> {
        serde_json::to_string_pretty(self)
            .map_err(|e| NetlistError::json_error("Failed to serialize circuit to JSON", Some(e)))
    }
}

impl Default for Circuit {
    fn default() -> Self {
        Self::new("Untitled Circuit")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pin_type_conversion() {
        assert_eq!(PinType::from_str("input"), PinType::Input);
        assert_eq!(PinType::from_str("INPUT"), PinType::Input);
        assert_eq!(PinType::from_str("unknown"), PinType::Unspecified);

        assert_eq!(PinType::Input.to_kicad_str(), "input");
        assert_eq!(PinType::Unspecified.to_kicad_str(), "passive");
    }

    #[test]
    fn test_component_creation() {
        let mut component = Component::new("R1", "Device:R", "10k");
        component.add_pin(PinInfo::passive("1", "~"));
        component.add_pin(PinInfo::passive("2", "~"));

        assert_eq!(component.reference, "R1");
        assert_eq!(component.library().unwrap(), "Device");
        assert_eq!(component.part().unwrap(), "R");
        assert_eq!(component.pins.len(), 2);
    }

    #[test]
    fn test_net_operations() {
        let mut net = Net::new("VCC");
        let node = NetNode::new("R1", PinInfo::passive("1", "~"));
        net.add_node(node);

        assert!(!net.is_empty());
        assert_eq!(net.connected_components(), vec!["R1"]);
    }

    #[test]
    fn test_circuit_hierarchy() {
        let mut main_circuit = Circuit::new("Main");
        let mut sub_circuit = Circuit::new("SubCircuit");

        sub_circuit.add_component(Component::new("U1", "MCU:STM32", "STM32F407"));
        main_circuit.add_subcircuit(sub_circuit);

        let all_components = main_circuit.all_components();
        assert!(all_components.contains_key("/SubCircuit/U1"));
    }
}
