//! S-expression generation for KiCad schematic files using lexpr
//!
//! This module handles the conversion of circuit data to KiCad's S-expression format
//! using the lexpr crate for proper S-expression handling.

use crate::types::*;
use lexpr::{sexp, Value};
use log::{debug, info};

/// Round a floating point number to 4 decimal places
/// This prevents floating point precision issues like 117.94999999999999
fn round_coord(value: f64) -> f64 {
    (value * 10000.0).round() / 10000.0
}

/// Generate a complete KiCad schematic S-expression using lexpr
pub fn generate_schematic_sexp(
    circuit_data: &CircuitData,
    hierarchical_labels: &[HierarchicalLabel],
    config: &SchematicConfig,
) -> Result<String, SchematicError> {
    info!("🔄 Generating complete KiCad schematic S-expression with lexpr");
    info!(
        "📊 Input: {} components, {} labels",
        circuit_data.components.len(),
        hierarchical_labels.len()
    );

    // Build the main schematic S-expression
    let mut schematic_parts = vec![
        Value::symbol("kicad_sch"),
        sexp!((version 20250114)),
        sexp!((generator "rust_kicad_schematic_writer")),
        sexp!((generator_version "0.1.0")),
        Value::list(vec![
            Value::symbol("uuid"),
            Value::string(config.uuid.clone()),
        ]),
        Value::list(vec![
            Value::symbol("paper"),
            Value::string(config.paper_size.clone()),
        ]),
    ];

    // Add lib_symbols section (empty for now)
    schematic_parts.push(sexp!((lib_symbols)));

    // Add components
    for component in &circuit_data.components {
        let component_sexp = generate_component_sexp(component, config)?;
        schematic_parts.push(component_sexp);
    }

    // Add hierarchical labels
    for label in hierarchical_labels {
        let label_sexp = generate_hierarchical_label_sexp(label)?;
        schematic_parts.push(label_sexp);
    }

    // Add sheet_instances
    schematic_parts.push(sexp!((sheet_instances
        (path "/" (page "1"))
    )));

    // Add embedded_fonts
    schematic_parts.push(sexp!((embedded_fonts no)));

    // Create the final S-expression
    let schematic_sexp = Value::list(schematic_parts);

    // Convert to string
    let result = lexpr::to_string(&schematic_sexp).map_err(|e| {
        SchematicError::SerializationError(format!("lexpr serialization failed: {}", e))
    })?;

    info!(
        "✅ S-expression generation completed, {} characters",
        result.len()
    );

    Ok(result)
}

/// Generate S-expression for a component using lexpr
fn generate_component_sexp(component: &Component, config: &SchematicConfig) -> Result<Value, SchematicError> {
    debug!(
        "🔧 Generating component S-expression: {} ({})",
        component.reference, component.lib_id
    );

    let component_uuid = uuid::Uuid::new_v4().to_string();

    // Extract values to avoid field access in sexp! macro
    let pos_x = round_coord(component.position.x);
    let pos_y = round_coord(component.position.y);
    let rotation = round_coord(component.rotation);
    let lib_id = component.lib_id.clone();
    let reference = component.reference.clone();
    let value = component.value.clone();
    let ref_y = round_coord(pos_y - 2.54);
    let val_y = round_coord(pos_y + 2.54);

    // Build the component S-expression using Value::list
    let mut component_parts = vec![
        Value::symbol("symbol"),
        Value::list(vec![
            Value::symbol("lib_id"),
            Value::string(lib_id),
        ]),
        sexp!((at, pos_x, pos_y, rotation)),
        sexp!((unit 1)),
        sexp!((exclude_from_sim no)),
        sexp!((in_bom yes)),
        sexp!((on_board yes)),
        sexp!((dnp no)),
        sexp!((fields_autoplaced yes)),
        Value::list(vec![
            Value::symbol("uuid"),
            Value::string(component_uuid.clone()),
        ]),
        sexp!((property "Reference" ,reference
            (at ,pos_x ,ref_y 0)
            (effects (font (size 1.27 1.27)))
        )),
        sexp!((property "Value" ,value
            (at ,pos_x ,val_y 0)
            (effects (font (size 1.27 1.27)))
        )),
    ];

    // Add pins
    for pin in &component.pins {
        let pin_number = pin.number.clone();
        let pin_uuid = uuid::Uuid::new_v4().to_string();
        let pin_sexp = Value::list(vec![
            Value::symbol("pin"),
            Value::string(pin_number),
            Value::list(vec![
                Value::symbol("uuid"),
                Value::string(pin_uuid),
            ]),
        ]);
        component_parts.push(pin_sexp);
    }

    // Add instances
    let ref_for_instances = component.reference.clone();
    let project_name = config.title.clone();
    component_parts.push(sexp!((instances
        (project ,project_name
            (path "/"
                (reference ,ref_for_instances)
                (unit 1)
            )
        )
    )));

    let component_sexp = Value::list(component_parts);

    debug!(
        "✅ Component S-expression generated for {}",
        component.reference
    );
    Ok(component_sexp)
}

/// Generate S-expression for a hierarchical label using lexpr
fn generate_hierarchical_label_sexp(label: &HierarchicalLabel) -> Result<Value, SchematicError> {
    debug!(
        "🏷️  Generating hierarchical label S-expression: '{}' at ({:.2}, {:.2})",
        label.name, label.position.x, label.position.y
    );

    // Extract values to avoid field access in sexp! macro
    let name = label.name.clone();
    let shape = label.shape.to_kicad_string();
    let pos_x = round_coord(label.position.x);
    let pos_y = round_coord(label.position.y);
    let orientation = round_coord(label.orientation);
    let font_size = round_coord(label.effects.font_size);
    let justify = label.effects.justify.clone();
    let uuid = label.uuid.clone();

    let label_sexp = Value::list(vec![
        Value::symbol("hierarchical_label"),
        Value::string(name),
        Value::list(vec![
            Value::symbol("shape"),
            Value::symbol(shape),
        ]),
        Value::list(vec![
            Value::symbol("at"),
            Value::from(pos_x),
            Value::from(pos_y),
            Value::from(orientation),
        ]),
        Value::list(vec![
            Value::symbol("effects"),
            Value::list(vec![
                Value::symbol("font"),
                Value::list(vec![
                    Value::symbol("size"),
                    Value::from(font_size),
                    Value::from(font_size),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("justify"),
                Value::symbol(&*justify),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("uuid"),
            Value::string(uuid),
        ]),
    ]);

    debug!(
        "✅ Hierarchical label S-expression generated for '{}'",
        label.name
    );
    Ok(label_sexp)
}

/// Generate a minimal component S-expression for testing
pub fn generate_test_component_sexp() -> Value {
    sexp!((symbol
        (lib_id "Device:R")
        (at 100.0 100.0 0)
        (unit 1)
        (exclude_from_sim no)
        (in_bom yes)
        (on_board yes)
        (dnp no)
        (uuid "test-uuid-1234")
        (property "Reference" "R1"
            (at 100.0 97.46 0)
            (effects (font (size 1.27 1.27)))
        )
        (property "Value" "1k"
            (at 100.0 102.54 0)
            (effects (font (size 1.27 1.27)))
        )
        (pin "1" (uuid "pin-uuid-1"))
        (pin "2" (uuid "pin-uuid-2"))
        (instances
            (project "test_project"
                (path "/" (reference "R1") (unit 1))
            )
        )
    ))
}

/// Generate a test hierarchical label S-expression
pub fn generate_test_hierarchical_label_sexp() -> Value {
    sexp!((hierarchical_label "VCC"
        (shape input)
        (at 95.25 58.42 90)
        (effects
            (font (size 1.27 1.27))
            (justify left)
        )
        (uuid "test-label-uuid-1234")
    ))
}

/// Generate a complete test schematic S-expression
pub fn generate_test_schematic_sexp() -> Value {
    let component_sexp = generate_test_component_sexp();
    let label_sexp = generate_test_hierarchical_label_sexp();

    let parts = vec![
        Value::symbol("kicad_sch"),
        sexp!((version 20250114)),
        sexp!((generator "rust_kicad_schematic_writer")),
        sexp!((generator_version "0.1.0")),
        sexp!((uuid "test-schematic-uuid")),
        sexp!((paper "A4")),
        sexp!((lib_symbols)),
        component_sexp,
        label_sexp,
        sexp!((sheet_instances
            (path "/" (page "1"))
        )),
        sexp!((embedded_fonts no)),
    ];

    Value::list(parts)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_component_sexp_generation() {
        let mut component = Component::new(
            "R1".to_string(),
            "Device:R".to_string(),
            "1k".to_string(),
            Position { x: 100.0, y: 100.0 },
        );

        component.add_pin(Pin {
            number: "1".to_string(),
            name: "~".to_string(),
            x: 0.0,
            y: 3.81,
            orientation: 270.0,
        });

        let config = SchematicConfig::default();
        let sexp = generate_component_sexp(&component, &config).unwrap();
        let sexp_str = lexpr::to_string(&sexp).unwrap();

        assert!(sexp_str.contains("Device:R"));
        assert!(sexp_str.contains("R1"));
        assert!(sexp_str.contains("1k"));
    }

    #[test]
    fn test_hierarchical_label_sexp_generation() {
        let label =
            HierarchicalLabel::new("VCC".to_string(), Position { x: 95.25, y: 58.42 }, 90.0);

        let sexp = generate_hierarchical_label_sexp(&label).unwrap();
        let sexp_str = lexpr::to_string(&sexp).unwrap();

        assert!(sexp_str.contains("hierarchical_label"));
        assert!(sexp_str.contains("VCC"));
        assert!(sexp_str.contains("95.25"));
        assert!(sexp_str.contains("58.42"));
    }

    #[test]
    fn test_complete_schematic_generation() {
        let circuit_data = create_test_circuit();
        let labels = vec![
            HierarchicalLabel::new("VCC".to_string(), Position { x: 100.0, y: 95.0 }, 90.0),
            HierarchicalLabel::new("GND".to_string(), Position { x: 100.0, y: 105.0 }, 270.0),
        ];
        let config = SchematicConfig::default();

        let sexp_str = generate_schematic_sexp(&circuit_data, &labels, &config).unwrap();

        assert!(sexp_str.contains("kicad_sch"));
        assert!(sexp_str.contains("hierarchical_label"));
        assert!(sexp_str.contains("VCC"));
        assert!(sexp_str.contains("GND"));
        assert!(sexp_str.contains("sheet_instances"));
    }

    #[test]
    fn test_lexpr_sexp_macro() {
        let test_sexp = sexp!((hierarchical_label "TEST"
            (shape input)
            (at 100.0 100.0 0)
            (effects (font (size 1.27 1.27)))
        ));

        let sexp_str = lexpr::to_string(&test_sexp).unwrap();
        assert!(sexp_str.contains("hierarchical_label"));
        assert!(sexp_str.contains("TEST"));
    }

    fn create_test_circuit() -> CircuitData {
        let mut circuit = CircuitData::new("test_circuit".to_string());

        let mut component = Component::new(
            "R1".to_string(),
            "Device:R".to_string(),
            "1k".to_string(),
            Position { x: 100.0, y: 100.0 },
        );

        component.add_pin(Pin {
            number: "1".to_string(),
            name: "~".to_string(),
            x: 0.0,
            y: 3.81,
            orientation: 270.0,
        });

        component.add_pin(Pin {
            number: "2".to_string(),
            name: "~".to_string(),
            x: 0.0,
            y: -3.81,
            orientation: 90.0,
        });

        circuit.add_component(component);

        circuit
    }
}
