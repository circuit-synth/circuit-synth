use serde_json;
use std::collections::HashMap;

#[derive(Debug, Clone, serde::Deserialize)]
struct TestComponent {
    reference: String,
    symbol: String,
    value: String,
    footprint: String,
    datasheet: String,
    description: String,
    properties: HashMap<String, String>,
    pins: Vec<TestPinInfo>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct TestPinInfo {
    number: String,
    name: String,
    pin_type: String,
}

fn main() {
    let test_json = r#"
    {
        "reference": "U2",
        "symbol": "Regulator_Linear:AP1117-15",
        "value": "",
        "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        "datasheet": "",
        "description": "",
        "properties": {},
        "pins": [
            {
                "number": "3",
                "name": "VI",
                "pin_type": "passive"
            },
            {
                "number": "1",
                "name": "GND",
                "pin_type": "passive"
            },
            {
                "number": "2",
                "name": "VO",
                "pin_type": "passive"
            }
        ]
    }
    "#;

    match serde_json::from_str::<TestComponent>(test_json) {
        Ok(component) => {
            println!("Successfully deserialized component: {}", component.reference);
            println!("Number of pins: {}", component.pins.len());
            for pin in &component.pins {
                println!("  Pin {}: {} ({})", pin.number, pin.name, pin.pin_type);
            }
        }
        Err(e) => {
            println!("Deserialization error: {}", e);
        }
    }
}