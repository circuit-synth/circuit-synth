//! Performance benchmarks for reference generation
//! 
//! This benchmark suite measures the performance of various reference manager
//! operations to ensure we meet our performance targets.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use rust_reference_manager::{RustReferenceManager};
use std::collections::HashMap;

fn benchmark_reference_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("reference_generation");
    
    // Test different numbers of references
    for size in [100, 1000, 10000].iter() {
        group.bench_with_input(
            BenchmarkId::new("sequential_generation", size),
            size,
            |b, &size| {
                b.iter(|| {
                    let mut manager = RustReferenceManager::new();
                    for i in 0..size {
                        let prefix = match i % 3 {
                            0 => "R",
                            1 => "C",
                            _ => "L",
                        };
                        black_box(manager.generate_next_reference(prefix).unwrap());
                    }
                });
            },
        );
    }
    
    group.finish();
}

fn benchmark_reference_validation(c: &mut Criterion) {
    let mut group = c.benchmark_group("reference_validation");
    
    // Pre-populate manager with references
    let mut manager = RustReferenceManager::new();
    for i in 1..=10000 {
        let prefix = match i % 3 {
            0 => "R",
            1 => "C",
            _ => "L",
        };
        manager.generate_next_reference(prefix).unwrap();
    }
    
    group.bench_function("validate_existing", |b| {
        b.iter(|| {
            // Validate references that exist
            for i in 1..=100 {
                let reference = format!("R{}", i);
                black_box(manager.validate_reference(&reference));
            }
        });
    });
    
    group.bench_function("validate_non_existing", |b| {
        b.iter(|| {
            // Validate references that don't exist
            for i in 20000..20100 {
                let reference = format!("R{}", i);
                black_box(manager.validate_reference(&reference));
            }
        });
    });
    
    group.finish();
}

fn benchmark_hierarchy_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("hierarchy_operations");
    
    group.bench_function("get_all_used_references", |b| {
        let mut manager = RustReferenceManager::new();
        
        // Pre-populate with references
        for i in 1..=1000 {
            let prefix = match i % 5 {
                0 => "R",
                1 => "C",
                2 => "L",
                3 => "U",
                _ => "D",
            };
            manager.generate_next_reference(prefix).unwrap();
        }
        
        b.iter(|| {
            black_box(manager.get_all_used_references());
        });
    });
    
    group.finish();
}

fn benchmark_initial_counters(c: &mut Criterion) {
    let mut group = c.benchmark_group("initial_counters");
    
    group.bench_function("with_large_initial_counters", |b| {
        let mut counters = HashMap::new();
        for i in 0..100 {
            counters.insert(format!("PREFIX_{}", i), 1000);
        }
        
        b.iter(|| {
            let manager = RustReferenceManager::with_initial_counters(black_box(counters.clone()));
            black_box(manager);
        });
    });
    
    group.bench_function("generation_with_high_counters", |b| {
        let mut counters = HashMap::new();
        counters.insert("R".to_string(), 50000);
        counters.insert("C".to_string(), 30000);
        counters.insert("L".to_string(), 20000);
        
        b.iter(|| {
            let mut manager = RustReferenceManager::with_initial_counters(counters.clone());
            
            // Generate references starting from high numbers
            for _ in 0..100 {
                black_box(manager.generate_next_reference("R").unwrap());
                black_box(manager.generate_next_reference("C").unwrap());
                black_box(manager.generate_next_reference("L").unwrap());
            }
        });
    });
    
    group.finish();
}

fn benchmark_unnamed_nets(c: &mut Criterion) {
    let mut group = c.benchmark_group("unnamed_nets");
    
    group.bench_function("generate_unnamed_nets", |b| {
        b.iter(|| {
            let mut manager = RustReferenceManager::new();
            for _ in 0..1000 {
                black_box(manager.generate_next_unnamed_net_name());
            }
        });
    });
    
    group.finish();
}

fn benchmark_mixed_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("mixed_operations");
    
    group.bench_function("realistic_workflow", |b| {
        b.iter(|| {
            let mut manager = RustReferenceManager::new();
            
            // Simulate a realistic workflow
            for i in 0..1000 {
                match i % 10 {
                    0..=5 => {
                        // Generate references (60% of operations)
                        let prefix = match i % 3 {
                            0 => "R",
                            1 => "C",
                            _ => "U",
                        };
                        black_box(manager.generate_next_reference(prefix).unwrap());
                    }
                    6..=8 => {
                        // Validate references (30% of operations)
                        let reference = format!("R{}", i / 2);
                        black_box(manager.validate_reference(&reference));
                    }
                    _ => {
                        // Generate unnamed nets (10% of operations)
                        black_box(manager.generate_next_unnamed_net_name());
                    }
                }
            }
        });
    });
    
    group.finish();
}

fn benchmark_concurrent_access(c: &mut Criterion) {
    let mut group = c.benchmark_group("concurrent_access");
    
    group.bench_function("parallel_validation", |b| {
        use std::sync::{Arc, Mutex};
        use std::thread;
        
        let mut manager = RustReferenceManager::new();
        
        // Pre-populate with references
        for i in 1..=10000 {
            manager.generate_next_reference("R").unwrap();
        }
        
        let manager = Arc::new(Mutex::new(manager));
        
        b.iter(|| {
            let mut handles = vec![];
            
            for thread_id in 0..4 {
                let manager_clone = Arc::clone(&manager);
                let handle = thread::spawn(move || {
                    let mgr = manager_clone.lock().unwrap();
                    for i in 0..100 {
                        let reference = format!("R{}", thread_id * 100 + i + 1);
                        black_box(mgr.validate_reference(&reference));
                    }
                });
                handles.push(handle);
            }
            
            for handle in handles {
                handle.join().unwrap();
            }
        });
    });
    
    group.finish();
}

fn benchmark_memory_usage(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_usage");
    
    group.bench_function("large_reference_set", |b| {
        b.iter(|| {
            let mut manager = RustReferenceManager::new();
            
            // Generate a large number of references to test memory efficiency
            for i in 0..50000 {
                let prefix = match i % 10 {
                    0 => "R", 1 => "C", 2 => "L", 3 => "U", 4 => "D",
                    5 => "Q", 6 => "IC", 7 => "SW", 8 => "J", _ => "TP",
                };
                black_box(manager.generate_next_reference(prefix).unwrap());
            }
            
            // Test operations on large dataset
            black_box(manager.get_all_used_references().len());
            black_box(manager.validate_reference("R25000"));
        });
    });
    
    group.finish();
}

fn benchmark_error_handling(c: &mut Criterion) {
    let mut group = c.benchmark_group("error_handling");
    
    group.bench_function("invalid_prefix_handling", |b| {
        b.iter(|| {
            let mut manager = RustReferenceManager::new();
            
            // Test various invalid prefixes
            let invalid_prefixes = ["", "123", "R-", "@#$", "N$"];
            
            for prefix in &invalid_prefixes {
                let result = manager.generate_next_reference(prefix);
                black_box(result.is_err());
            }
        });
    });
    
    group.bench_function("duplicate_registration", |b| {
        b.iter(|| {
            let mut manager = RustReferenceManager::new();
            
            // Register a reference
            manager.register_reference("R1").unwrap();
            
            // Try to register the same reference multiple times
            for _ in 0..100 {
                let result = manager.register_reference("R1");
                black_box(result.is_err());
            }
        });
    });
    
    group.finish();
}

criterion_group!(
    benches,
    benchmark_reference_generation,
    benchmark_reference_validation,
    benchmark_hierarchy_operations,
    benchmark_initial_counters,
    benchmark_unnamed_nets,
    benchmark_mixed_operations,
    benchmark_concurrent_access,
    benchmark_memory_usage,
    benchmark_error_handling
);

criterion_main!(benches);