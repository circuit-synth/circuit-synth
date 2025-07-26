//! High-performance collision detection for component placement
//! 
//! This module provides optimized collision detection algorithms with spatial
//! indexing for O(n log n) performance instead of naive O(n²) checking.

use crate::types::{Component, BoundingBox, Point};
use std::collections::HashMap;
use rayon::prelude::*;

/// High-performance collision detector with spatial indexing
pub struct CollisionDetector {
    spacing: f64,
    grid_size: f64,
}

impl CollisionDetector {
    /// Create a new collision detector with the given minimum spacing
    pub fn new(spacing: f64) -> Self {
        Self {
            spacing,
            grid_size: spacing * 2.0, // Grid cells are 2x the minimum spacing
        }
    }

    /// Detect all collisions between components using spatial indexing
    /// Returns pairs of component indices that are colliding
    pub fn detect_collisions(&self, components: &[Component]) -> Vec<(usize, usize)> {
        if components.len() < 2 {
            return Vec::new();
        }

        // Use spatial grid for efficient collision detection
        let grid = self.build_spatial_grid(components);
        let mut collisions = Vec::new();

        // Check collisions within each grid cell and adjacent cells
        for cell_components in grid.values() {
            if cell_components.len() < 2 {
                continue;
            }

            // Check all pairs within this cell
            for i in 0..cell_components.len() {
                for j in (i + 1)..cell_components.len() {
                    let idx1 = cell_components[i];
                    let idx2 = cell_components[j];
                    
                    if self.check_collision_pair(&components[idx1], &components[idx2]) {
                        collisions.push((idx1, idx2));
                    }
                }
            }
        }

        // Also check adjacent cells to catch collisions at cell boundaries
        self.check_adjacent_cell_collisions(components, &grid, &mut collisions);

        collisions
    }

    /// Check if two specific components are colliding
    pub fn check_collision(&self, comp1: &Component, comp2: &Component) -> bool {
        self.check_collision_pair(comp1, comp2)
    }

    /// Build spatial grid for efficient collision detection
    fn build_spatial_grid(&self, components: &[Component]) -> HashMap<(i32, i32), Vec<usize>> {
        let mut grid: HashMap<(i32, i32), Vec<usize>> = HashMap::new();

        for (idx, component) in components.iter().enumerate() {
            let grid_x = (component.position.x / self.grid_size).floor() as i32;
            let grid_y = (component.position.y / self.grid_size).floor() as i32;
            
            grid.entry((grid_x, grid_y))
                .or_default()
                .push(idx);
        }

        grid
    }

    /// Check collisions between adjacent grid cells
    fn check_adjacent_cell_collisions(
        &self,
        components: &[Component],
        grid: &HashMap<(i32, i32), Vec<usize>>,
        collisions: &mut Vec<(usize, usize)>,
    ) {
        // Define adjacent cell offsets
        let adjacent_offsets = [
            (1, 0), (0, 1), (1, 1), (-1, 1), // Right, Up, Up-Right, Up-Left
        ];

        for (&(grid_x, grid_y), cell_components) in grid {
            for &offset in &adjacent_offsets {
                let adjacent_cell = (grid_x + offset.0, grid_y + offset.1);
                
                if let Some(adjacent_components) = grid.get(&adjacent_cell) {
                    // Check collisions between current cell and adjacent cell
                    for &idx1 in cell_components {
                        for &idx2 in adjacent_components {
                            if idx1 < idx2 && self.check_collision_pair(&components[idx1], &components[idx2]) {
                                collisions.push((idx1, idx2));
                            }
                        }
                    }
                }
            }
        }
    }

    /// Check if two components are colliding (optimized)
    #[inline]
    fn check_collision_pair(&self, comp1: &Component, comp2: &Component) -> bool {
        // Fast distance check first
        let dx = comp2.position.x - comp1.position.x;
        let dy = comp2.position.y - comp1.position.y;
        let distance_squared = dx * dx + dy * dy;
        
        // Quick rejection test using circular approximation
        let min_distance = self.spacing + (comp1.width + comp1.height + comp2.width + comp2.height) / 4.0;
        if distance_squared > min_distance * min_distance {
            return false;
        }

        // More precise bounding box collision detection
        let bbox1 = comp1.bounding_box().expand(self.spacing / 2.0);
        let bbox2 = comp2.bounding_box().expand(self.spacing / 2.0);
        
        bbox1.intersects(&bbox2)
    }

    /// Detect collisions in parallel for large component sets
    pub fn detect_collisions_parallel(&self, components: &[Component]) -> Vec<(usize, usize)> {
        if components.len() < 100 {
            // Use sequential version for small sets
            return self.detect_collisions(components);
        }

        // Divide components into chunks for parallel processing
        let chunk_size = (components.len() / rayon::current_num_threads()).max(50);
        let chunks: Vec<_> = components.chunks(chunk_size).enumerate().collect();

        // Process chunks in parallel
        let chunk_collisions: Vec<Vec<(usize, usize)>> = chunks
            .par_iter()
            .map(|(chunk_idx, chunk)| {
                let mut collisions = Vec::new();
                let base_idx = chunk_idx * chunk_size;

                // Check collisions within this chunk
                for i in 0..chunk.len() {
                    for j in (i + 1)..chunk.len() {
                        if self.check_collision_pair(&chunk[i], &chunk[j]) {
                            collisions.push((base_idx + i, base_idx + j));
                        }
                    }
                }

                // Check collisions with components in later chunks
                for (other_chunk_idx, other_chunk) in chunks.iter().skip(chunk_idx + 1) {
                    let other_base_idx = other_chunk_idx * chunk_size;
                    
                    for (i, comp1) in chunk.iter().enumerate() {
                        for (j, comp2) in other_chunk.iter().enumerate() {
                            if self.check_collision_pair(comp1, comp2) {
                                collisions.push((base_idx + i, other_base_idx + j));
                            }
                        }
                    }
                }

                collisions
            })
            .collect();

        // Flatten results
        chunk_collisions.into_iter().flatten().collect()
    }

    /// Get collision statistics for debugging
    pub fn get_collision_stats(&self, components: &[Component]) -> CollisionStats {
        let collisions = self.detect_collisions(components);
        let total_pairs = components.len() * (components.len() - 1) / 2;
        
        CollisionStats {
            total_components: components.len(),
            total_collisions: collisions.len(),
            collision_rate: if total_pairs > 0 {
                collisions.len() as f64 / total_pairs as f64
            } else {
                0.0
            },
            average_spacing: self.calculate_average_spacing(components),
            min_spacing: self.calculate_min_spacing(components),
        }
    }

    /// Calculate average spacing between all component pairs
    fn calculate_average_spacing(&self, components: &[Component]) -> f64 {
        if components.len() < 2 {
            return 0.0;
        }

        let mut total_distance = 0.0;
        let mut pair_count = 0;

        for i in 0..components.len() {
            for j in (i + 1)..components.len() {
                total_distance += components[i].position.distance_to(&components[j].position);
                pair_count += 1;
            }
        }

        if pair_count > 0 {
            total_distance / pair_count as f64
        } else {
            0.0
        }
    }

    /// Calculate minimum spacing between any two components
    fn calculate_min_spacing(&self, components: &[Component]) -> f64 {
        if components.len() < 2 {
            return f64::INFINITY;
        }

        let mut min_distance = f64::INFINITY;

        for i in 0..components.len() {
            for j in (i + 1)..components.len() {
                let distance = components[i].position.distance_to(&components[j].position);
                min_distance = min_distance.min(distance);
            }
        }

        min_distance
    }
}

/// Collision detection statistics
#[derive(Debug, Clone)]
pub struct CollisionStats {
    pub total_components: usize,
    pub total_collisions: usize,
    pub collision_rate: f64,
    pub average_spacing: f64,
    pub min_spacing: f64,
}

impl CollisionStats {
    pub fn is_acceptable(&self, min_spacing: f64) -> bool {
        self.total_collisions == 0 && self.min_spacing >= min_spacing
    }
}

/// Specialized collision detector for courtyard-based detection
pub struct CourtyardCollisionDetector {
    base_detector: CollisionDetector,
    courtyard_margin: f64,
}

impl CourtyardCollisionDetector {
    pub fn new(spacing: f64, courtyard_margin: f64) -> Self {
        Self {
            base_detector: CollisionDetector::new(spacing),
            courtyard_margin,
        }
    }

    /// Check collision using component courtyards (more accurate for real PCB components)
    pub fn check_courtyard_collision(&self, comp1: &Component, comp2: &Component) -> bool {
        // Expand bounding boxes by courtyard margin
        let courtyard1 = comp1.bounding_box().expand(self.courtyard_margin);
        let courtyard2 = comp2.bounding_box().expand(self.courtyard_margin);
        
        courtyard1.intersects(&courtyard2)
    }

    /// Detect all courtyard collisions
    pub fn detect_courtyard_collisions(&self, components: &[Component]) -> Vec<(usize, usize)> {
        let mut collisions = Vec::new();

        for i in 0..components.len() {
            for j in (i + 1)..components.len() {
                if self.check_courtyard_collision(&components[i], &components[j]) {
                    collisions.push((i, j));
                }
            }
        }

        collisions
    }
}

/// Optimized collision resolution utilities
pub mod resolution {
    use super::*;
    use crate::types::Force;

    /// Calculate optimal separation vector for two colliding components
    pub fn calculate_separation_vector(
        comp1: &Component,
        comp2: &Component,
        min_spacing: f64,
    ) -> (f64, f64) {
        let dx = comp2.position.x - comp1.position.x;
        let dy = comp2.position.y - comp1.position.y;
        let distance = (dx * dx + dy * dy).sqrt();

        if distance < 0.01 {
            // Components are on top of each other, use random separation
            use rand::Rng;
            let mut rng = rand::thread_rng();
            let angle = rng.gen::<f64>() * 2.0 * std::f64::consts::PI;
            return (angle.cos() * min_spacing, angle.sin() * min_spacing);
        }

        // Calculate required separation
        let required_distance = min_spacing + (comp1.width + comp2.width) / 2.0;
        let separation_needed = required_distance - distance;

        if separation_needed > 0.0 {
            let unit_dx = dx / distance;
            let unit_dy = dy / distance;
            (unit_dx * separation_needed, unit_dy * separation_needed)
        } else {
            (0.0, 0.0)
        }
    }

    /// Apply separation force to resolve collision
    pub fn apply_separation_force(
        comp1: &mut Component,
        comp2: &mut Component,
        separation: (f64, f64),
        force_ratio: f64,
    ) {
        let half_sep_x = separation.0 * force_ratio / 2.0;
        let half_sep_y = separation.1 * force_ratio / 2.0;

        comp1.position.x -= half_sep_x;
        comp1.position.y -= half_sep_y;
        comp2.position.x += half_sep_x;
        comp2.position.y += half_sep_y;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_collision_detector_creation() {
        let detector = CollisionDetector::new(2.0);
        assert_eq!(detector.spacing, 2.0);
        assert_eq!(detector.grid_size, 4.0);
    }

    #[test]
    fn test_no_collision_detection() {
        let detector = CollisionDetector::new(2.0);
        
        let components = vec![
            Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(0.0, 0.0))
                .with_size(2.0, 1.0),
            Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(10.0, 0.0))
                .with_size(2.0, 1.0),
        ];
        
        let collisions = detector.detect_collisions(&components);
        assert!(collisions.is_empty());
    }

    #[test]
    fn test_collision_detection() {
        let detector = CollisionDetector::new(2.0);
        
        let components = vec![
            Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(0.0, 0.0))
                .with_size(2.0, 1.0),
            Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(1.0, 0.0))
                .with_size(2.0, 1.0),
        ];
        
        let collisions = detector.detect_collisions(&components);
        assert_eq!(collisions.len(), 1);
        assert_eq!(collisions[0], (0, 1));
    }

    #[test]
    fn test_collision_stats() {
        let detector = CollisionDetector::new(2.0);
        
        let components = vec![
            Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(0.0, 0.0)),
            Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
                .with_position(Point::new(5.0, 0.0)),
        ];
        
        let stats = detector.get_collision_stats(&components);
        assert_eq!(stats.total_components, 2);
        assert_eq!(stats.total_collisions, 0);
        assert_eq!(stats.min_spacing, 5.0);
    }

    #[test]
    fn test_courtyard_collision_detector() {
        let detector = CourtyardCollisionDetector::new(2.0, 1.0);
        
        let comp1 = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0))
            .with_size(2.0, 1.0);
        let comp2 = Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(2.5, 0.0))
            .with_size(2.0, 1.0);
        
        // Should collide due to courtyard margin
        assert!(detector.check_courtyard_collision(&comp1, &comp2));
    }
}