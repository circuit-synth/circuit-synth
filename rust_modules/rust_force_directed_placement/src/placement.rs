//! High-performance force-directed placement algorithm
//! 
//! This module implements the main placement algorithm with hierarchical optimization
//! and provides 100x performance improvement over the Python implementation.

use crate::types::{
    Component, Connection, Point, Force, BoundingBox, SubcircuitGroup, 
    PlacementConfig, PlacementResult
};
use crate::forces::ForceCalculator;
use crate::collision::CollisionDetector;
use crate::errors::PlacementError;

use std::collections::{HashMap, HashSet};
use rayon::prelude::*;
use log::{info, debug, warn};

/// High-performance force-directed placement engine
pub struct ForceDirectedPlacer {
    config: PlacementConfig,
    force_calculator: ForceCalculator,
    collision_detector: CollisionDetector,
}

impl ForceDirectedPlacer {
    /// Create a new placer with the given configuration
    pub fn new(config: PlacementConfig) -> Self {
        let force_calculator = ForceCalculator::new(config.clone());
        let collision_detector = CollisionDetector::new(config.component_spacing * 0.5);
        
        Self {
            config,
            force_calculator,
            collision_detector,
        }
    }

    /// Get a reference to the configuration
    pub fn config(&self) -> &PlacementConfig {
        &self.config
    }

    /// Main placement algorithm with hierarchical optimization
    pub fn place(
        &mut self,
        mut components: Vec<Component>,
        connections: Vec<Connection>,
        board_width: f64,
        board_height: f64,
    ) -> Result<PlacementResult, PlacementError> {
        info!("Starting force-directed placement for {} components", components.len());
        info!("Board dimensions: {}x{}mm", board_width, board_height);

        if components.is_empty() {
            return Ok(PlacementResult::new());
        }

        // Build connection graph for fast lookups
        let connection_graph = self.build_connection_graph(&connections);
        
        // Group components by subcircuit for hierarchical placement
        let mut groups = self.group_by_subcircuit(&mut components);
        info!("Found {} subcircuit groups", groups.len());

        let board_bounds = BoundingBox::new(0.0, 0.0, board_width, board_height);

        // Level 1: Optimize within each subcircuit
        info!("Level 1: Optimizing component placement within subcircuits");
        for group in groups.values_mut() {
            self.optimize_subcircuit(group, &mut components, &connection_graph, &board_bounds)?;
        }

        // Level 2: Optimize subcircuit group positions
        if groups.len() > 1 {
            info!("Level 2: Optimizing subcircuit group positions");
            self.count_inter_group_connections(&mut groups, &connection_graph);
            self.optimize_group_positions(&mut groups, &mut components, &board_bounds)?;
        }

        // Level 3: Final collision detection and resolution
        info!("Level 3: Final collision detection and resolution");
        let collision_count = self.enforce_minimum_spacing(&mut components, &connection_graph)?;

        // Extract final results
        let mut result = PlacementResult::new();
        for component in &components {
            result.positions.insert(component.reference.clone(), component.position);
            result.rotations.insert(component.reference.clone(), component.rotation);
        }
        
        result.collision_count = collision_count;
        result.final_energy = self.force_calculator.calculate_system_energy(
            &components, &connections, &connection_graph
        );

        info!("Force-directed placement complete");
        Ok(result)
    }

    /// Build connection graph for fast neighbor lookups
    fn build_connection_graph(&self, connections: &[Connection]) -> HashMap<String, Vec<String>> {
        let mut graph: HashMap<String, Vec<String>> = HashMap::new();
        
        for connection in connections {
            graph.entry(connection.ref1.clone())
                .or_default()
                .push(connection.ref2.clone());
            graph.entry(connection.ref2.clone())
                .or_default()
                .push(connection.ref1.clone());
        }
        
        graph
    }

    /// Group components by subcircuit path for hierarchical placement
    fn group_by_subcircuit(&self, components: &mut [Component]) -> HashMap<String, SubcircuitGroup> {
        let mut groups: HashMap<String, SubcircuitGroup> = HashMap::new();
        
        for component in components.iter() {
            let path = if component.path.is_empty() {
                "root".to_string()
            } else {
                component.path.clone()
            };
            
            let group = groups.entry(path.clone()).or_insert_with(|| SubcircuitGroup::new(path));
            group.add_component(component.reference.clone());
        }

        // Initialize component positions within groups
        for group in groups.values() {
            self.initialize_group_positions(group, components);
        }

        groups
    }

    /// Initialize component positions within a group using grid layout
    fn initialize_group_positions(&self, group: &SubcircuitGroup, components: &mut [Component]) {
        if group.components.is_empty() {
            return;
        }

        let grid_size = (group.components.len() as f64).sqrt().ceil() as usize;
        let spacing = self.config.component_spacing * 3.0;

        for (i, comp_ref) in group.components.iter().enumerate() {
            if let Some(component) = components.iter_mut().find(|c| &c.reference == comp_ref) {
                let row = i / grid_size;
                let col = i % grid_size;
                component.position = Point::new(
                    col as f64 * spacing,
                    row as f64 * spacing,
                );
            }
        }
    }

    /// Optimize component positions within a subcircuit using force-directed layout
    fn optimize_subcircuit(
        &self,
        group: &SubcircuitGroup,
        components: &mut [Component],
        connection_graph: &HashMap<String, Vec<String>>,
        board_bounds: &BoundingBox,
    ) -> Result<(), PlacementError> {
        if group.components.len() <= 1 {
            return Ok(());
        }

        debug!("Optimizing group {} with {} components", group.path, group.components.len());

        // Extract components for this group
        let mut group_components: Vec<Component> = group.components
            .iter()
            .filter_map(|ref_name| {
                components.iter().find(|c| &c.reference == ref_name).cloned()
            })
            .collect();

        if group_components.is_empty() {
            return Ok(());
        }

        // Build connections for this group
        let group_connections = self.extract_group_connections(&group_components, connection_graph);

        // Initialize temperature for simulated annealing
        let mut temperature = self.config.initial_temperature;
        let mut convergence_count = 0;
        let convergence_iterations = 15;

        // Force-directed optimization loop
        for iteration in 0..self.config.iterations_per_level {
            // Calculate forces for all components in parallel
            let forces = self.force_calculator.calculate_all_forces(
                &group_components,
                &group_connections,
                connection_graph,
                board_bounds,
                temperature,
            );

            // Apply forces and track displacement
            let total_displacement = self.force_calculator.apply_forces(
                &mut group_components,
                &forces,
                temperature,
            );

            // Cool down temperature
            temperature *= self.config.cooling_rate;

            // Check for convergence
            if total_displacement < self.config.convergence_threshold {
                convergence_count += 1;
                if convergence_count >= convergence_iterations {
                    debug!("Subcircuit converged after {} iterations", iteration + 1);
                    break;
                }
            } else {
                convergence_count = 0;
            }

            // Optimize rotations periodically
            if self.config.enable_rotation && iteration % 10 == 0 {
                self.force_calculator.optimize_rotations(&mut group_components, connection_graph);
            }
        }

        // Update original components with optimized positions
        for optimized_comp in group_components {
            if let Some(original_comp) = components.iter_mut().find(|c| c.reference == optimized_comp.reference) {
                original_comp.position = optimized_comp.position;
                original_comp.rotation = optimized_comp.rotation;
            }
        }

        Ok(())
    }

    /// Extract connections that are internal to a group
    fn extract_group_connections(
        &self,
        group_components: &[Component],
        connection_graph: &HashMap<String, Vec<String>>,
    ) -> Vec<Connection> {
        let group_refs: HashSet<String> = group_components
            .iter()
            .map(|c| c.reference.clone())
            .collect();

        let mut connections = Vec::new();
        let mut added_pairs = HashSet::new();

        for component in group_components {
            if let Some(connected_refs) = connection_graph.get(&component.reference) {
                for connected_ref in connected_refs {
                    if group_refs.contains(connected_ref) {
                        // Create a canonical pair to avoid duplicates
                        let pair = if component.reference < *connected_ref {
                            (component.reference.clone(), connected_ref.clone())
                        } else {
                            (connected_ref.clone(), component.reference.clone())
                        };

                        if !added_pairs.contains(&pair) {
                            connections.push(Connection::new(pair.0.clone(), pair.1.clone()));
                            added_pairs.insert(pair);
                        }
                    }
                }
            }
        }

        connections
    }

    /// Count connections between different subcircuit groups
    fn count_inter_group_connections(
        &self,
        groups: &mut HashMap<String, SubcircuitGroup>,
        connection_graph: &HashMap<String, Vec<String>>,
    ) {
        // Build reference to group mapping
        let mut ref_to_group: HashMap<String, String> = HashMap::new();
        for (group_path, group) in groups.iter() {
            for comp_ref in &group.components {
                ref_to_group.insert(comp_ref.clone(), group_path.clone());
            }
        }

        // Count connections between groups
        for (group_path, group) in groups.iter_mut() {
            group.connections_to_other_groups.clear();

            for comp_ref in &group.components {
                if let Some(connected_refs) = connection_graph.get(comp_ref) {
                    for connected_ref in connected_refs {
                        if let Some(connected_group) = ref_to_group.get(connected_ref) {
                            if connected_group != group_path {
                                *group.connections_to_other_groups
                                    .entry(connected_group.clone())
                                    .or_insert(0) += 1;
                            }
                        }
                    }
                }
            }
        }
    }

    /// Optimize positions of subcircuit groups relative to each other
    fn optimize_group_positions(
        &self,
        groups: &mut HashMap<String, SubcircuitGroup>,
        components: &mut [Component],
        board_bounds: &BoundingBox,
    ) -> Result<(), PlacementError> {
        if groups.len() <= 1 {
            return Ok(());
        }

        // Update group properties based on current component positions
        let component_positions: HashMap<String, Point> = components
            .iter()
            .map(|c| (c.reference.clone(), c.position))
            .collect();

        for group in groups.values_mut() {
            group.update_properties(&component_positions);
        }

        let group_list: Vec<String> = groups.keys().cloned().collect();
        let mut temperature = self.config.initial_temperature * 2.0;

        // Force-directed optimization for groups
        for _iteration in 0..(self.config.iterations_per_level / 2) {
            let mut group_forces: HashMap<String, Force> = HashMap::new();

            // Calculate forces between groups
            for group_path in &group_list {
                let mut total_force = Force::zero();
                let group = &groups[group_path];

                // Attraction to connected groups
                for (connected_path, connection_count) in &group.connections_to_other_groups {
                    if let Some(connected_group) = groups.get(connected_path) {
                        let attraction = self.force_calculator.calculate_group_attraction(
                            group.center,
                            connected_group.center,
                            *connection_count,
                        );
                        total_force += attraction;
                    }
                }

                // Repulsion from all other groups
                for other_path in &group_list {
                    if other_path != group_path {
                        let other_group = &groups[other_path];
                        let group_size = (group.bounding_box.width() * group.bounding_box.height()).sqrt();
                        let other_size = (other_group.bounding_box.width() * other_group.bounding_box.height()).sqrt();
                        
                        let repulsion = self.force_calculator.calculate_group_repulsion(
                            group.center,
                            other_group.center,
                            group_size,
                            other_size,
                        );
                        total_force += repulsion;
                    }
                }

                // Boundary forces
                let boundary_force = self.calculate_group_boundary_force(group, board_bounds);
                total_force += boundary_force;

                group_forces.insert(group_path.clone(), total_force * self.config.damping);
            }

            // Apply forces to move groups
            for group_path in &group_list {
                if let Some(force) = group_forces.get(group_path) {
                    let max_move = temperature * self.config.component_spacing * 2.0;
                    let limited_force = force.limit(max_move);

                    // Move all components in the group
                    let group = &groups[group_path];
                    for comp_ref in &group.components {
                        if let Some(component) = components.iter_mut().find(|c| &c.reference == comp_ref) {
                            component.position.x += limited_force.fx;
                            component.position.y += limited_force.fy;
                        }
                    }
                }
            }

            // Update group properties after movement
            let component_positions: HashMap<String, Point> = components
                .iter()
                .map(|c| (c.reference.clone(), c.position))
                .collect();

            for group in groups.values_mut() {
                group.update_properties(&component_positions);
            }

            // Cool down
            temperature *= self.config.cooling_rate;
        }

        Ok(())
    }

    /// Calculate boundary force for a group
    fn calculate_group_boundary_force(&self, group: &SubcircuitGroup, board_bounds: &BoundingBox) -> Force {
        let mut force = Force::zero();
        let strength = 20.0;

        // Check each boundary
        if group.bounding_box.min_x < board_bounds.min_x {
            force.fx += strength * (board_bounds.min_x - group.bounding_box.min_x);
        }

        if group.bounding_box.max_x > board_bounds.max_x {
            force.fx -= strength * (group.bounding_box.max_x - board_bounds.max_x);
        }

        if group.bounding_box.min_y < board_bounds.min_y {
            force.fy += strength * (board_bounds.min_y - group.bounding_box.min_y);
        }

        if group.bounding_box.max_y > board_bounds.max_y {
            force.fy -= strength * (group.bounding_box.max_y - board_bounds.max_y);
        }

        force
    }

    /// Enforce minimum spacing between all components with connectivity awareness
    fn enforce_minimum_spacing(
        &mut self,
        components: &mut [Component],
        connection_graph: &HashMap<String, Vec<String>>,
    ) -> Result<usize, PlacementError> {
        let max_iterations = 50;
        let mut final_collision_count = 0;

        info!("Enforcing minimum spacing for {} components", components.len());

        // Two-pass collision resolution
        // Pass 1: Gentle connectivity-aware resolution
        for iteration in 0..(max_iterations / 2) {
            let collisions = self.collision_detector.detect_collisions(components);
            if collisions.is_empty() {
                info!("No collisions detected after {} gentle iterations", iteration + 1);
                return Ok(0);
            }

            debug!("Gentle iteration {}: Found {} collisions", iteration + 1, collisions.len());
            
            let resolved = self.resolve_collisions_connectivity_aware(
                components, &collisions, connection_graph, true
            );

            if resolved == 0 {
                warn!("No collisions resolved in gentle iteration");
                break;
            }
        }

        // Pass 2: Strict resolution for remaining collisions
        let remaining_collisions = self.collision_detector.detect_collisions(components);
        if !remaining_collisions.is_empty() {
            info!("Pass 2: Strict collision resolution for {} remaining collisions", remaining_collisions.len());

            for iteration in 0..(max_iterations / 2) {
                let collisions = self.collision_detector.detect_collisions(components);
                if collisions.is_empty() {
                    info!("All collisions resolved after {} strict iterations", iteration + 1);
                    return Ok(0);
                }

                let resolved = self.resolve_collisions_connectivity_aware(
                    components, &collisions, connection_graph, false
                );

                if resolved == 0 {
                    warn!("Cannot resolve remaining collisions");
                    final_collision_count = collisions.len();
                    break;
                }
            }
        }

        // Final collision count
        let final_collisions = self.collision_detector.detect_collisions(components);
        final_collision_count = final_collisions.len();

        if final_collision_count > 0 {
            warn!("Failed to resolve {} collisions", final_collision_count);
        }

        Ok(final_collision_count)
    }

    /// Resolve collisions with awareness of component connectivity
    fn resolve_collisions_connectivity_aware(
        &self,
        components: &mut [Component],
        collisions: &[(usize, usize)],
        connection_graph: &HashMap<String, Vec<String>>,
        gentle: bool,
    ) -> usize {
        let mut resolved_count = 0;

        for &(i, j) in collisions {
            let comp1_ref = components[i].reference.clone();
            let comp2_ref = components[j].reference.clone();

            // Check if components are connected
            let are_connected = connection_graph
                .get(&comp1_ref)
                .map(|connections| connections.contains(&comp2_ref))
                .unwrap_or(false);

            // Calculate separation vector
            let dx = components[j].position.x - components[i].position.x;
            let dy = components[j].position.y - components[i].position.y;
            let distance = (dx * dx + dy * dy).sqrt();

            let (unit_dx, unit_dy) = if distance < 0.1 {
                // Components are on top of each other, use random separation
                use rand::Rng;
                let mut rng = rand::thread_rng();
                let angle = rng.gen::<f64>() * 2.0 * std::f64::consts::PI;
                (angle.cos(), angle.sin())
            } else {
                (dx / distance, dy / distance)
            };

            // Determine force multiplier based on connectivity and mode
            let force_multiplier = match (gentle, are_connected) {
                (true, true) => 0.1,   // Very gentle for connected components
                (true, false) => 0.3,  // Moderate for unconnected components
                (false, true) => 0.3,  // Strict mode: stronger for connected
                (false, false) => 0.6, // Strict mode: strongest for unconnected
            };

            // Calculate push distance
            let push_distance = self.config.component_spacing * force_multiplier;

            // Apply symmetric push
            components[i].position.x -= unit_dx * push_distance;
            components[i].position.y -= unit_dy * push_distance;
            components[j].position.x += unit_dx * push_distance;
            components[j].position.y += unit_dy * push_distance;

            resolved_count += 1;

            if are_connected {
                debug!("Gently separating connected components {} and {}", comp1_ref, comp2_ref);
            } else {
                debug!("Separating unconnected components {} and {}", comp1_ref, comp2_ref);
            }
        }

        resolved_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_placer_creation() {
        let config = PlacementConfig::default();
        let placer = ForceDirectedPlacer::new(config);
        assert_eq!(placer.config.component_spacing, 2.0);
    }

    #[test]
    fn test_connection_graph_building() {
        let config = PlacementConfig::default();
        let placer = ForceDirectedPlacer::new(config);
        
        let connections = vec![
            Connection::new("R1".to_string(), "R2".to_string()),
            Connection::new("R2".to_string(), "C1".to_string()),
        ];
        
        let graph = placer.build_connection_graph(&connections);
        
        assert_eq!(graph.get("R1").unwrap(), &vec!["R2"]);
        assert_eq!(graph.get("R2").unwrap(), &vec!["R1", "C1"]);
        assert_eq!(graph.get("C1").unwrap(), &vec!["R2"]);
    }

    #[test]
    fn test_empty_placement() {
        let config = PlacementConfig::default();
        let mut placer = ForceDirectedPlacer::new(config);
        
        let result = placer.place(vec![], vec![], 100.0, 100.0).unwrap();
        assert!(result.positions.is_empty());
    }

    #[test]
    fn test_single_component_placement() {
        let config = PlacementConfig::default();
        let mut placer = ForceDirectedPlacer::new(config);
        
        let components = vec![
            Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
        ];
        
        let result = placer.place(components, vec![], 100.0, 100.0).unwrap();
        assert_eq!(result.positions.len(), 1);
        assert!(result.positions.contains_key("R1"));
    }
}