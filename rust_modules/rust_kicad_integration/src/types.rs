//! Type definitions for KiCad schematic generation

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Errors that can occur during schematic generation
#[derive(Debug, thiserror::Error)]
pub enum SchematicError {
    #[error("Component not found: {0}")]
    ComponentNotFound(String),

    #[error("Pin not found: {0}")]
    PinNotFound(String),

    #[error("IO error: {0}")]
    IoError(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Invalid data: {0}")]
    InvalidData(String),

    #[error("Calculation error: {0}")]
    CalculationError(String),
}

/// Configuration for schematic generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchematicConfig {
    pub paper_size: String,
    pub title: String,
    pub company: String,
    pub version: String,
    pub generator: String,
    pub uuid: String,
}

impl Default for SchematicConfig {
    fn default() -> Self {
        Self {
            paper_size: "A4".to_string(),
            title: "Circuit Synth Generated Schematic".to_string(),
            company: "Circuit-Synth".to_string(),
            version: "20250114".to_string(),
            generator: "rust_kicad_schematic_writer".to_string(),
            uuid: uuid::Uuid::new_v4().to_string(),
        }
    }
}

/// 2D position in the schematic
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
}

/// Pin information for a component
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pin {
    pub number: String,
    pub name: String,
    pub x: f64,
    pub y: f64,
    pub orientation: f64, // degrees
}

/// Component in the circuit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub reference: String,
    pub lib_id: String,
    pub value: String,
    pub position: Position,
    pub rotation: f64, // degrees
    pub pins: Vec<Pin>,
}

/// Connection between a component pin and a net
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PinConnection {
    pub component_ref: String,
    pub pin_id: String,
}

/// Net in the circuit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Net {
    pub name: String,
    pub connected_pins: Vec<PinConnection>,
}

/// Complete circuit data with hierarchical support
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CircuitData {
    pub name: String,
    pub components: Vec<Component>,
    pub nets: Vec<Net>,
    /// Hierarchical subcircuits for complex designs
    #[serde(default)]
    pub subcircuits: Vec<CircuitData>,
}

/// Shape of a hierarchical label
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LabelShape {
    Input,
    Output,
    Bidirectional,
    TriState,
    Passive,
}

impl LabelShape {
    pub fn to_kicad_string(&self) -> &'static str {
        match self {
            LabelShape::Input => "input",
            LabelShape::Output => "output",
            LabelShape::Bidirectional => "bidirectional",
            LabelShape::TriState => "tri_state",
            LabelShape::Passive => "passive",
        }
    }
}

/// Effects for label text
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LabelEffects {
    pub font_size: f64,
    pub justify: String,
}

/// Hierarchical label in the schematic
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HierarchicalLabel {
    pub name: String,
    pub shape: LabelShape,
    pub position: Position,
    pub orientation: f64, // degrees
    pub effects: LabelEffects,
    pub uuid: String,
}

/// Symbol instance for the new KiCad format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolInstance {
    pub project: String,
    pub path: String,
    pub reference: String,
    pub unit: i32,
}

/// Library symbol definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LibrarySymbol {
    pub lib_id: String,
    pub properties: HashMap<String, String>,
    pub graphics: Vec<GraphicElement>,
    pub pins: Vec<Pin>,
}

/// Graphic element in a symbol
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphicElement {
    pub element_type: String,
    pub points: Vec<Position>,
    pub stroke_width: f64,
    pub fill_type: String,
}

/// Sheet instance for hierarchical designs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SheetInstance {
    pub path: String,
    pub page: String,
}

impl CircuitData {
    /// Create a new empty circuit
    pub fn new(name: String) -> Self {
        Self {
            name,
            components: Vec::new(),
            nets: Vec::new(),
            subcircuits: Vec::new(),
        }
    }

    /// Add a component to the circuit
    pub fn add_component(&mut self, component: Component) {
        self.components.push(component);
    }

    /// Add a net to the circuit
    pub fn add_net(&mut self, net: Net) {
        self.nets.push(net);
    }

    /// Add a subcircuit to the circuit
    pub fn add_subcircuit(&mut self, subcircuit: CircuitData) {
        self.subcircuits.push(subcircuit);
    }

    /// Get total number of pin connections across all nets (including subcircuits)
    pub fn total_connections(&self) -> usize {
        let local_connections = self
            .nets
            .iter()
            .map(|net| net.connected_pins.len())
            .sum::<usize>();
        let subcircuit_connections = self
            .subcircuits
            .iter()
            .map(|sc| sc.total_connections())
            .sum::<usize>();
        local_connections + subcircuit_connections
    }

    /// Get total number of components (including subcircuits)
    pub fn total_components(&self) -> usize {
        let local_components = self.components.len();
        let subcircuit_components = self
            .subcircuits
            .iter()
            .map(|sc| sc.total_components())
            .sum::<usize>();
        local_components + subcircuit_components
    }

    /// Get total number of nets (including subcircuits)
    pub fn total_nets(&self) -> usize {
        let local_nets = self.nets.len();
        let subcircuit_nets = self
            .subcircuits
            .iter()
            .map(|sc| sc.total_nets())
            .sum::<usize>();
        local_nets + subcircuit_nets
    }

    /// Find a component by reference (searches recursively through subcircuits)
    pub fn find_component(&self, reference: &str) -> Option<&Component> {
        // First search local components
        if let Some(component) = self.components.iter().find(|c| c.reference == reference) {
            return Some(component);
        }

        // Then search subcircuits recursively
        for subcircuit in &self.subcircuits {
            if let Some(component) = subcircuit.find_component(reference) {
                return Some(component);
            }
        }

        None
    }

    /// Find a net by name (searches recursively through subcircuits)
    pub fn find_net(&self, name: &str) -> Option<&Net> {
        // First search local nets
        if let Some(net) = self.nets.iter().find(|n| n.name == name) {
            return Some(net);
        }

        // Then search subcircuits recursively
        for subcircuit in &self.subcircuits {
            if let Some(net) = subcircuit.find_net(name) {
                return Some(net);
            }
        }

        None
    }

    /// Get all components recursively (flattened from all subcircuits)
    pub fn get_all_components(&self) -> Vec<&Component> {
        let mut all_components = Vec::new();

        // Add local components
        all_components.extend(self.components.iter());

        // Add components from subcircuits recursively
        for subcircuit in &self.subcircuits {
            all_components.extend(subcircuit.get_all_components());
        }

        all_components
    }

    /// Get all nets recursively (flattened from all subcircuits)
    pub fn get_all_nets(&self) -> Vec<&Net> {
        let mut all_nets = Vec::new();

        // Add local nets
        all_nets.extend(self.nets.iter());

        // Add nets from subcircuits recursively
        for subcircuit in &self.subcircuits {
            all_nets.extend(subcircuit.get_all_nets());
        }

        all_nets
    }

    /// Check if this circuit has hierarchical structure
    pub fn is_hierarchical(&self) -> bool {
        !self.subcircuits.is_empty()
    }

    /// Get hierarchical statistics
    pub fn get_hierarchy_stats(&self) -> HierarchyStats {
        let mut stats = HierarchyStats {
            total_levels: 1,
            total_subcircuits: self.subcircuits.len(),
            max_depth: 1,
            total_components: self.components.len(),
            total_nets: self.nets.len(),
        };

        for subcircuit in &self.subcircuits {
            let sub_stats = subcircuit.get_hierarchy_stats();
            stats.total_subcircuits += sub_stats.total_subcircuits;
            stats.max_depth = stats.max_depth.max(sub_stats.max_depth + 1);
            stats.total_components += sub_stats.total_components;
            stats.total_nets += sub_stats.total_nets;
        }

        stats
    }
}

/// Statistics about circuit hierarchy
#[derive(Debug, Clone)]
pub struct HierarchyStats {
    pub total_levels: usize,
    pub total_subcircuits: usize,
    pub max_depth: usize,
    pub total_components: usize,
    pub total_nets: usize,
}

impl Component {
    /// Create a new component
    pub fn new(reference: String, lib_id: String, value: String, position: Position) -> Self {
        Self {
            reference,
            lib_id,
            value,
            position,
            rotation: 0.0,
            pins: Vec::new(),
        }
    }

    /// Add a pin to the component
    pub fn add_pin(&mut self, pin: Pin) {
        self.pins.push(pin);
    }

    /// Find a pin by number or name
    pub fn find_pin(&self, identifier: &str) -> Option<&Pin> {
        self.pins
            .iter()
            .find(|p| p.number == identifier || p.name == identifier)
    }
}

impl Net {
    /// Create a new net
    pub fn new(name: String) -> Self {
        Self {
            name,
            connected_pins: Vec::new(),
        }
    }

    /// Add a pin connection to the net
    pub fn add_connection(&mut self, component_ref: String, pin_id: String) {
        self.connected_pins.push(PinConnection {
            component_ref,
            pin_id,
        });
    }
}

impl HierarchicalLabel {
    /// Create a new hierarchical label
    pub fn new(name: String, position: Position, orientation: f64) -> Self {
        Self {
            name,
            shape: LabelShape::Input,
            position,
            orientation,
            effects: LabelEffects {
                font_size: 1.27,
                justify: "center".to_string(),
            },
            uuid: uuid::Uuid::new_v4().to_string(),
        }
    }

    /// Set the label shape
    pub fn with_shape(mut self, shape: LabelShape) -> Self {
        self.shape = shape;
        self
    }

    /// Set the label effects
    pub fn with_effects(mut self, effects: LabelEffects) -> Self {
        self.effects = effects;
        self
    }
}
