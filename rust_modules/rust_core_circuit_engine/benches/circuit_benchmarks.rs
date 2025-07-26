//! Benchmarks for Circuit operations
//! 
//! These benchmarks measure the performance improvements of the Rust implementation
//! compared to the Python baseline, targeting 10-100x improvements.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use rust_core_circuit_engine::{Circuit, Component, Net, ReferenceManager};

fn bench_circuit_creation(c: &mut Criterion) {
    c.bench_function("circuit_creation", |b| {
        b.iter(|| {
            Circuit::new(
                Some(black_box("BenchCircuit".to_string())),
                Some(black_box("Benchmark circuit".to_string()))
            ).unwrap()
        })
    });
}

fn bench_component_addition(c: &mut Criterion) {
    let mut group = c.benchmark_group("component_addition");
    
    for size in [10, 100, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("final_references", size), size, |b, &size| {
            b.iter(|| {
                let mut circuit = Circuit::with_capacity("BenchCircuit".to_string(), size, size / 2);
                
                for i in 1..=size {
                    let component = Component::new(
                        black_box("Device:R".to_string()),
                        Some(black_box(format!("R{}", i))),
                        Some(black_box(format!("{}k", i * 10))),
                        None,
                        None,
                        None,
                        None,
                    ).unwrap();
                    
                    circuit.add_component(component).unwrap();
                }
                
                circuit
            })
        });
        
        group.bench_with_input(BenchmarkId::new("prefix_references", size), size, |b, &size| {
            b.iter(|| {
                let mut circuit = Circuit::with_capacity("BenchCircuit".to_string(), size, size / 2);
                
                for i in 1..=size {
                    let component = Component::new(
                        black_box("Device:R".to_string()),
                        Some(black_box("R".to_string())),  // Prefix only
                        Some(black_box(format!("{}k", i * 10))),
                        None,
                        None,
                        None,
                        None,
                    ).unwrap();
                    
                    circuit.add_component(component).unwrap();
                }
                
                circuit
            })
        });
    }
    
    group.finish();
}

fn bench_reference_finalization(c: &mut Criterion) {
    let mut group = c.benchmark_group("reference_finalization");
    
    for size in [10, 100, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("finalize", size), size, |b, &size| {
            b.iter_batched(
                || {
                    let mut circuit = Circuit::with_capacity("BenchCircuit".to_string(), size, size / 2);
                    
                    // Add components with prefix references
                    for i in 1..=size {
                        let component = Component::new(
                            "Device:R".to_string(),
                            Some("R".to_string()),  // Prefix only
                            Some(format!("{}k", i * 10)),
                            None,
                            None,
                            None,
                            None,
                        ).unwrap();
                        
                        circuit.add_component(component).unwrap();
                    }
                    
                    circuit
                },
                |mut circuit| {
                    circuit.finalize_references().unwrap();
                    circuit
                },
                criterion::BatchSize::SmallInput
            )
        });
    }
    
    group.finish();
}

fn bench_netlist_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("netlist_generation");
    
    for size in [10, 100, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("text_netlist", size), size, |b, &size| {
            b.iter_batched(
                || {
                    let mut circuit = Circuit::with_capacity("BenchCircuit".to_string(), size, size / 2);
                    
                    // Add components
                    for i in 1..=size {
                        let component = Component::new(
                            "Device:R".to_string(),
                            Some(format!("R{}", i)),
                            Some(format!("{}k", i * 10)),
                            None,
                            None,
                            None,
                            None,
                        ).unwrap();
                        
                        circuit.add_component(component).unwrap();
                    }
                    
                    // Add nets
                    for i in 1..=size/2 {
                        let net = Net::new(Some(format!("NET{}", i))).unwrap();
                        circuit.add_net(net).unwrap();
                    }
                    
                    circuit
                },
                |circuit| {
                    black_box(circuit.generate_text_netlist().unwrap())
                },
                criterion::BatchSize::SmallInput
            )
        });
    }
    
    group.finish();
}

fn bench_component_creation(c: &mut Criterion) {
    let mut group = c.benchmark_group("component_creation");
    
    group.bench_function("basic_resistor", |b| {
        b.iter(|| {
            Component::new(
                black_box("Device:R".to_string()),
                Some(black_box("R1".to_string())),
                Some(black_box("10k".to_string())),
                None,
                None,
                None,
                None,
            ).unwrap()
        })
    });
    
    group.bench_function("with_extra_fields", |b| {
        b.iter(|| {
            // Note: This would need to be adapted for actual kwargs handling
            Component::new(
                black_box("Device:R".to_string()),
                Some(black_box("R1".to_string())),
                Some(black_box("10k".to_string())),
                Some(black_box("0805".to_string())),
                Some(black_box("http://example.com/datasheet".to_string())),
                Some(black_box("Test resistor".to_string())),
                None,
            ).unwrap()
        })
    });
    
    group.finish();
}

fn bench_reference_manager(c: &mut Criterion) {
    let mut group = c.benchmark_group("reference_manager");
    
    for size in [100, 1000, 10000].iter() {
        group.bench_with_input(BenchmarkId::new("reference_generation", size), size, |b, &size| {
            b.iter_batched(
                || ReferenceManager::with_capacity(size, 10),
                |mut manager| {
                    for _ in 0..size {
                        black_box(manager.generate_next_reference("R".to_string()).unwrap());
                    }
                    manager
                },
                criterion::BatchSize::SmallInput
            )
        });
        
        group.bench_with_input(BenchmarkId::new("reference_validation", size), size, |b, &size| {
            b.iter_batched(
                || {
                    let mut manager = ReferenceManager::with_capacity(size, 10);
                    // Pre-populate with references
                    for i in 1..=size {
                        manager.register_reference(format!("R{}", i)).unwrap();
                    }
                    manager
                },
                |manager| {
                    for i in 1..=size {
                        black_box(manager.validate_reference(&format!("R{}", i)).unwrap());
                    }
                    manager
                },
                criterion::BatchSize::SmallInput
            )
        });
    }
    
    group.finish();
}

fn bench_net_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("net_operations");
    
    group.bench_function("net_creation", |b| {
        b.iter(|| {
            Net::new(Some(black_box("VCC".to_string()))).unwrap()
        })
    });
    
    group.bench_function("net_with_auto_name", |b| {
        b.iter(|| {
            Net::new(None).unwrap()
        })
    });
    
    group.finish();
}

fn bench_bulk_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("bulk_operations");
    
    for size in [100, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("bulk_component_addition", size), size, |b, &size| {
            b.iter_batched(
                || {
                    let mut components = Vec::with_capacity(size);
                    for i in 1..=size {
                        let component = Component::new(
                            "Device:R".to_string(),
                            Some(format!("R{}", i)),
                            Some(format!("{}k", i * 10)),
                            None,
                            None,
                            None,
                            None,
                        ).unwrap();
                        components.push(component);
                    }
                    (Circuit::with_capacity("BenchCircuit".to_string(), size, size / 2), components)
                },
                |(mut circuit, components)| {
                    black_box(circuit.bulk_add_components(components).unwrap());
                    circuit
                },
                criterion::BatchSize::SmallInput
            )
        });
    }
    
    group.finish();
}

fn bench_hierarchical_circuits(c: &mut Criterion) {
    c.bench_function("hierarchical_finalization", |b| {
        b.iter_batched(
            || {
                let mut parent = Circuit::new(Some("Parent".to_string()), None).unwrap();
                
                // Create subcircuits with components
                for sub_i in 1..=5 {
                    let mut subcircuit = Circuit::new(Some(format!("Sub{}", sub_i)), None).unwrap();
                    
                    for comp_i in 1..=10 {
                        let component = Component::new(
                            "Device:R".to_string(),
                            Some("R".to_string()),  // Prefix
                            Some(format!("{}k", comp_i * 10)),
                            None,
                            None,
                            None,
                            None,
                        ).unwrap();
                        subcircuit.add_component(component).unwrap();
                    }
                    
                    parent.add_subcircuit(subcircuit).unwrap();
                }
                
                parent
            },
            |mut circuit| {
                circuit.finalize_references().unwrap();
                circuit
            },
            criterion::BatchSize::SmallInput
        )
    });
}

fn bench_memory_efficiency(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_efficiency");
    
    group.bench_function("large_circuit_creation", |b| {
        b.iter(|| {
            let mut circuit = Circuit::with_capacity("LargeCircuit".to_string(), 10000, 5000);
            
            // Add many components
            for i in 1..=1000 {
                let component = Component::new(
                    "Device:R".to_string(),
                    Some(format!("R{}", i)),
                    Some(format!("{}k", i)),
                    None,
                    None,
                    None,
                    None,
                ).unwrap();
                circuit.add_component(component).unwrap();
            }
            
            // Add many nets
            for i in 1..=500 {
                let net = Net::new(Some(format!("NET{}", i))).unwrap();
                circuit.add_net(net).unwrap();
            }
            
            black_box(circuit)
        })
    });
    
    group.finish();
}

criterion_group!(
    benches,
    bench_circuit_creation,
    bench_component_addition,
    bench_reference_finalization,
    bench_netlist_generation,
    bench_component_creation,
    bench_reference_manager,
    bench_net_operations,
    bench_bulk_operations,
    bench_hierarchical_circuits,
    bench_memory_efficiency
);

criterion_main!(benches);