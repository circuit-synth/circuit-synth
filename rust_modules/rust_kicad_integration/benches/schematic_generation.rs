//! Benchmarks for schematic generation performance
//!
//! Run with: cargo bench

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use rust_kicad_schematic_writer::{
    schematic_api::*,
    CircuitData, Component, Net, PinConnection, Pin, Position,
    RustSchematicWriter, SchematicConfig,
};

fn bench_minimal_schematic(c: &mut Criterion) {
    c.bench_function("create_minimal_schematic", |b| {
        b.iter(|| {
            let schematic = create_minimal_schematic();
            black_box(schematic);
        });
    });
}

fn bench_empty_schematic_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("empty_schematic_paper_sizes");
    
    for size in &["A4", "A3", "A2", "Letter"] {
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            size,
            |b, &size| {
                b.iter(|| {
                    let schematic = create_empty_schematic(size);
                    black_box(schematic);
                });
            },
        );
    }
    group.finish();
}

fn bench_circuit_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("circuit_generation");
    
    // Small circuit (5 components)
    let small_circuit = create_circuit_with_n_components(5);
    group.bench_function("small_circuit_5_components", |b| {
        b.iter(|| {
            let config = SchematicConfig::default();
            let writer = RustSchematicWriter::new(small_circuit.clone(), config);
            let sexp = writer.generate_schematic_sexp().unwrap();
            black_box(sexp);
        });
    });
    
    // Medium circuit (50 components)
    let medium_circuit = create_circuit_with_n_components(50);
    group.bench_function("medium_circuit_50_components", |b| {
        b.iter(|| {
            let config = SchematicConfig::default();
            let writer = RustSchematicWriter::new(medium_circuit.clone(), config);
            let sexp = writer.generate_schematic_sexp().unwrap();
            black_box(sexp);
        });
    });
    
    // Large circuit (200 components)
    let large_circuit = create_circuit_with_n_components(200);
    group.bench_function("large_circuit_200_components", |b| {
        b.iter(|| {
            let config = SchematicConfig::default();
            let writer = RustSchematicWriter::new(large_circuit.clone(), config);
            let sexp = writer.generate_schematic_sexp().unwrap();
            black_box(sexp);
        });
    });
    
    group.finish();
}

fn bench_hierarchical_label_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("hierarchical_labels");
    
    for n_nets in &[10, 50, 100] {
        let circuit = create_circuit_with_n_nets(*n_nets);
        group.bench_function(format!("{}_nets", n_nets), |b| {
            b.iter(|| {
                let config = SchematicConfig::default();
                let mut writer = RustSchematicWriter::new(circuit.clone(), config);
                let labels = writer.generate_hierarchical_labels().unwrap();
                black_box(labels);
            });
        });
    }
    
    group.finish();
}

fn bench_hierarchical_circuit(c: &mut Criterion) {
    c.bench_function("hierarchical_circuit_3_levels", |b| {
        let circuit = create_hierarchical_circuit(3, 5);
        b.iter(|| {
            let config = SchematicConfig::default();
            let mut writer = RustSchematicWriter::new(circuit.clone(), config);
            let labels = writer.generate_hierarchical_labels().unwrap();
            let sexp = writer.generate_schematic_sexp().unwrap();
            black_box((labels, sexp));
        });
    });
}

// Helper functions to create test circuits

fn create_circuit_with_n_components(n: usize) -> CircuitData {
    let mut components = Vec::with_capacity(n);
    let mut nets = Vec::new();
    
    for i in 0..n {
        components.push(Component {
            reference: format!("R{}", i),
            lib_id: "Device:R".to_string(),
            value: "1k".to_string(),
            position: Position {
                x: (i as f64) * 10.0,
                y: (i as f64) * 10.0,
            },
            rotation: 0.0,
            pins: vec![
                Pin {
                    number: "1".to_string(),
                    name: "~".to_string(),
                    x: -3.81,
                    y: 0.0,
                    orientation: 180.0,
                },
                Pin {
                    number: "2".to_string(),
                    name: "~".to_string(),
                    x: 3.81,
                    y: 0.0,
                    orientation: 0.0,
                },
            ],
        });
        
        if i < n - 1 {
            nets.push(Net {
                name: format!("NET{}", i),
                connected_pins: vec![
                    PinConnection {
                        component_ref: format!("R{}", i),
                        pin_id: "2".to_string(),
                    },
                    PinConnection {
                        component_ref: format!("R{}", i + 1),
                        pin_id: "1".to_string(),
                    },
                ],
            });
        }
    }
    
    CircuitData {
        name: format!("circuit_{}_components", n),
        components,
        nets,
        subcircuits: Vec::new(),
    }
}

fn create_circuit_with_n_nets(n: usize) -> CircuitData {
    let mut nets = Vec::with_capacity(n);
    let mut components = Vec::new();
    
    for i in 0..n {
        components.push(Component {
            reference: format!("U{}", i),
            lib_id: "Device:R".to_string(),
            value: "1k".to_string(),
            position: Position {
                x: (i as f64) * 10.0,
                y: 100.0,
            },
            rotation: 0.0,
            pins: vec![
                Pin {
                    number: "1".to_string(),
                    name: "~".to_string(),
                    x: 0.0,
                    y: -3.81,
                    orientation: 90.0,
                },
            ],
        });
        
        nets.push(Net {
            name: format!("NET{}", i),
            connected_pins: vec![
                PinConnection {
                    component_ref: format!("U{}", i),
                    pin_id: "1".to_string(),
                },
            ],
        });
    }
    
    CircuitData {
        name: format!("circuit_{}_nets", n),
        components,
        nets,
        subcircuits: Vec::new(),
    }
}

fn create_hierarchical_circuit(depth: usize, width: usize) -> CircuitData {
    if depth == 0 {
        return CircuitData {
            name: "leaf".to_string(),
            components: vec![Component {
                reference: "R1".to_string(),
                lib_id: "Device:R".to_string(),
                value: "1k".to_string(),
                position: Position { x: 100.0, y: 100.0 },
                rotation: 0.0,
                pins: vec![],
            }],
            nets: vec![],
            subcircuits: Vec::new(),
        };
    }
    
    let mut subcircuits = Vec::with_capacity(width);
    for i in 0..width {
        let mut sub = create_hierarchical_circuit(depth - 1, width);
        sub.name = format!("sub_{}_{}", depth, i);
        subcircuits.push(sub);
    }
    
    CircuitData {
        name: format!("level_{}", depth),
        components: vec![],
        nets: vec![],
        subcircuits,
    }
}

criterion_group!(
    benches,
    bench_minimal_schematic,
    bench_empty_schematic_sizes,
    bench_circuit_generation,
    bench_hierarchical_label_generation,
    bench_hierarchical_circuit
);
criterion_main!(benches);