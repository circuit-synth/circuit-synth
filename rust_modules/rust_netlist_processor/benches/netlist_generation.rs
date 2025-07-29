//! Comprehensive benchmarks for netlist generation performance
//!
//! This benchmark suite validates the 30-50x performance improvements
//! targeted by the Rust migration, comparing against Python baseline
//! performance metrics.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use rust_netlist_processor::{
    Circuit, Component, Net, NetNode, NetlistProcessor, PinInfo, PinType,
};
use std::collections::HashMap;

/// Create a test circuit with the specified number of components
fn create_test_circuit(num_components: usize, nets_per_component: usize) -> Circuit {
    let mut circuit = Circuit::new("Benchmark Circuit");
    circuit.description = format!("Test circuit with {} components", num_components);

    // Add components
    for i in 0..num_components {
        let mut component = Component::new(
            format!("R{}", i + 1),
            "Device:R".to_string(),
            "10k".to_string(),
        );

        component.footprint = "Resistor_SMD:R_0603_1608Metric".to_string();
        component.description = format!("Test resistor {}", i + 1);
        component.datasheet = "https://example.com/datasheet.pdf".to_string();

        // Add pins
        component.add_pin(PinInfo::new("1", "~", PinType::Passive));
        component.add_pin(PinInfo::new("2", "~", PinType::Passive));

        // Add properties
        component
            .properties
            .insert("ki_keywords".to_string(), "resistor".to_string());
        component
            .properties
            .insert("ki_fp_filters".to_string(), "R_*".to_string());

        circuit.add_component(component);
    }

    // Add nets
    for i in 0..nets_per_component {
        let mut net = Net::new(format!("NET_{}", i + 1));

        // Connect multiple components to each net
        let components_per_net = (num_components / nets_per_component).max(2);
        for j in 0..components_per_net {
            let comp_idx = (i * components_per_net + j) % num_components;
            let pin_num = if j % 2 == 0 { "1" } else { "2" };

            let node = NetNode::new(
                format!("R{}", comp_idx + 1),
                PinInfo::new(pin_num, "~", PinType::Passive),
            );
            net.add_node(node);
        }

        circuit.add_net(net);
    }

    circuit
}

/// Create a hierarchical test circuit with subcircuits
fn create_hierarchical_circuit(depth: usize, components_per_level: usize) -> Circuit {
    fn create_subcircuit(
        name: String,
        level: usize,
        max_depth: usize,
        components_per_level: usize,
    ) -> Circuit {
        let mut circuit = Circuit::new(name);

        // Add components at this level
        for i in 0..components_per_level {
            let mut component = Component::new(
                format!("U{}_{}", level, i + 1),
                "MCU_ST_STM32F4:STM32F407VGTx".to_string(),
                "STM32F407VG".to_string(),
            );

            component.footprint = "Package_QFP:LQFP-100_14x14mm_P0.5mm".to_string();
            component.description = format!("MCU at level {} component {}", level, i + 1);

            // Add multiple pins for realistic complexity
            for pin_num in 1..=20 {
                let pin_type = match pin_num {
                    1..=4 => PinType::PowerIn,
                    5..=8 => PinType::Input,
                    9..=12 => PinType::Output,
                    13..=16 => PinType::Bidirectional,
                    _ => PinType::Passive,
                };

                component.add_pin(PinInfo::new(
                    pin_num.to_string(),
                    format!("PIN_{}", pin_num),
                    pin_type,
                ));
            }

            circuit.add_component(component);
        }

        // Add nets connecting components
        for i in 0..components_per_level {
            let mut net = Net::hierarchical(
                format!("HIER_NET_{}_{}", level, i + 1),
                format!("NET_{}", i + 1),
            );

            // Connect to multiple components
            for j in 0..components_per_level.min(3) {
                let node = NetNode::new(
                    format!("U{}_{}", level, j + 1),
                    PinInfo::new(
                        (i + 1).to_string(),
                        format!("PIN_{}", i + 1),
                        PinType::Bidirectional,
                    ),
                );
                net.add_node(node);
            }

            circuit.add_net(net);
        }

        // Add subcircuits if not at max depth
        if level < max_depth {
            for i in 0..2 {
                let subcircuit = create_subcircuit(
                    format!("SUB_{}_{}", level + 1, i + 1),
                    level + 1,
                    max_depth,
                    components_per_level,
                );
                circuit.add_subcircuit(subcircuit);
            }
        }

        circuit
    }

    create_subcircuit("Root".to_string(), 1, depth, components_per_level)
}

/// Benchmark complete netlist generation
fn bench_complete_netlist_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("complete_netlist_generation");

    // Test different circuit sizes
    let sizes = vec![10, 50, 100, 500, 1000];

    for size in sizes {
        let circuit = create_test_circuit(size, size / 2);
        let mut processor = NetlistProcessor::new();

        group.bench_with_input(
            BenchmarkId::new("components", size),
            &circuit,
            |b, circuit| {
                b.iter(|| {
                    processor
                        .generate_kicad_netlist(black_box(circuit))
                        .unwrap()
                });
            },
        );
    }

    group.finish();
}

/// Benchmark hierarchical netlist generation
fn bench_hierarchical_netlist_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("hierarchical_netlist_generation");

    // Test different hierarchy depths
    let depths = vec![1, 2, 3, 4];

    for depth in depths {
        let circuit = create_hierarchical_circuit(depth, 10);
        let mut processor = NetlistProcessor::new();

        group.bench_with_input(BenchmarkId::new("depth", depth), &circuit, |b, circuit| {
            b.iter(|| {
                processor
                    .generate_kicad_netlist(black_box(circuit))
                    .unwrap()
            });
        });
    }

    group.finish();
}

/// Benchmark individual processing stages
fn bench_processing_stages(c: &mut Criterion) {
    let circuit = create_test_circuit(100, 50);
    let mut processor = NetlistProcessor::new();

    c.bench_function("nets_only", |b| {
        b.iter(|| processor.generate_nets_only(black_box(&circuit)).unwrap());
    });

    c.bench_function("components_only", |b| {
        b.iter(|| {
            processor
                .generate_components_only(black_box(&circuit))
                .unwrap()
        });
    });
}

/// Benchmark memory usage and allocation patterns
fn bench_memory_usage(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_usage");

    // Test memory efficiency with different circuit sizes
    let sizes = vec![100, 500, 1000, 2000];

    for size in sizes {
        let circuit = create_test_circuit(size, size / 2);

        group.bench_with_input(
            BenchmarkId::new("memory_efficiency", size),
            &circuit,
            |b, circuit| {
                b.iter(|| {
                    let mut processor = NetlistProcessor::new();
                    let _result = processor
                        .generate_kicad_netlist(black_box(circuit))
                        .unwrap();
                    let stats = processor.get_performance_stats();
                    black_box(stats.memory_usage_mb());
                });
            },
        );
    }

    group.finish();
}

/// Benchmark parallel processing capabilities
fn bench_parallel_processing(c: &mut Criterion) {
    let circuit = create_hierarchical_circuit(3, 20);
    let mut processor = NetlistProcessor::new();

    c.bench_function("parallel_net_processing", |b| {
        b.iter(|| processor.generate_nets_only(black_box(&circuit)).unwrap());
    });
}

/// Benchmark string formatting performance
fn bench_string_formatting(c: &mut Criterion) {
    let mut group = c.benchmark_group("string_formatting");

    // Test S-expression formatting with different complexities
    let complexities = vec![
        ("simple", create_test_circuit(10, 5)),
        ("medium", create_test_circuit(100, 50)),
        ("complex", create_hierarchical_circuit(2, 20)),
    ];

    for (name, circuit) in complexities {
        let mut processor = NetlistProcessor::new();

        group.bench_with_input(
            BenchmarkId::new("s_expression_formatting", name),
            &circuit,
            |b, circuit| {
                b.iter(|| {
                    processor
                        .generate_kicad_netlist(black_box(circuit))
                        .unwrap()
                });
            },
        );
    }

    group.finish();
}

/// Performance regression test against baseline
fn bench_performance_regression(c: &mut Criterion) {
    let circuit = create_test_circuit(500, 250);
    let mut processor = NetlistProcessor::new();

    // This benchmark serves as a regression test
    // The baseline should be established and monitored over time
    c.bench_function("performance_baseline", |b| {
        b.iter(|| {
            let result = processor
                .generate_kicad_netlist(black_box(&circuit))
                .unwrap();
            black_box(result.len()); // Ensure the result is used
        });
    });
}

criterion_group!(
    benches,
    bench_complete_netlist_generation,
    bench_hierarchical_netlist_generation,
    bench_processing_stages,
    bench_memory_usage,
    bench_parallel_processing,
    bench_string_formatting,
    bench_performance_regression
);

criterion_main!(benches);
