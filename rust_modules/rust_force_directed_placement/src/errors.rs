//! Error types for force-directed placement operations

use thiserror::Error;

/// Errors that can occur during placement operations
#[derive(Error, Debug)]
pub enum PlacementError {
    #[error("Invalid component configuration: {message}")]
    InvalidComponent { message: String },

    #[error("Invalid board dimensions: width={width}, height={height}")]
    InvalidBoardDimensions { width: f64, height: f64 },

    #[error("Placement failed to converge after {iterations} iterations")]
    ConvergenceFailure { iterations: usize },

    #[error("Too many collisions detected: {count} unresolved collisions")]
    TooManyCollisions { count: usize },

    #[error("Invalid placement configuration: {message}")]
    InvalidConfiguration { message: String },

    #[error("Component not found: {reference}")]
    ComponentNotFound { reference: String },

    #[error("Invalid connection: {ref1} -> {ref2}")]
    InvalidConnection { ref1: String, ref2: String },

    #[error("Memory allocation failed: {message}")]
    MemoryError { message: String },

    #[error("Parallel processing error: {message}")]
    ParallelError { message: String },

    #[error("IO error: {message}")]
    IoError { message: String },

    #[error("Serialization error: {message}")]
    SerializationError { message: String },
}

impl PlacementError {
    /// Create an invalid component error
    pub fn invalid_component(message: impl Into<String>) -> Self {
        Self::InvalidComponent {
            message: message.into(),
        }
    }

    /// Create an invalid board dimensions error
    pub fn invalid_board_dimensions(width: f64, height: f64) -> Self {
        Self::InvalidBoardDimensions { width, height }
    }

    /// Create a convergence failure error
    pub fn convergence_failure(iterations: usize) -> Self {
        Self::ConvergenceFailure { iterations }
    }

    /// Create a too many collisions error
    pub fn too_many_collisions(count: usize) -> Self {
        Self::TooManyCollisions { count }
    }

    /// Create an invalid configuration error
    pub fn invalid_configuration(message: impl Into<String>) -> Self {
        Self::InvalidConfiguration {
            message: message.into(),
        }
    }

    /// Create a component not found error
    pub fn component_not_found(reference: impl Into<String>) -> Self {
        Self::ComponentNotFound {
            reference: reference.into(),
        }
    }

    /// Create an invalid connection error
    pub fn invalid_connection(ref1: impl Into<String>, ref2: impl Into<String>) -> Self {
        Self::InvalidConnection {
            ref1: ref1.into(),
            ref2: ref2.into(),
        }
    }

    /// Create a memory error
    pub fn memory_error(message: impl Into<String>) -> Self {
        Self::MemoryError {
            message: message.into(),
        }
    }

    /// Create a parallel processing error
    pub fn parallel_error(message: impl Into<String>) -> Self {
        Self::ParallelError {
            message: message.into(),
        }
    }

    /// Create an IO error
    pub fn io_error(message: impl Into<String>) -> Self {
        Self::IoError {
            message: message.into(),
        }
    }

    /// Create a serialization error
    pub fn serialization_error(message: impl Into<String>) -> Self {
        Self::SerializationError {
            message: message.into(),
        }
    }
}

/// Result type for placement operations
pub type PlacementResult<T> = Result<T, PlacementError>;

/// Validation utilities for placement inputs
pub mod validation {
    use super::*;
    use crate::types::{Component, Connection, PlacementConfig};

    /// Validate a component
    pub fn validate_component(component: &Component) -> PlacementResult<()> {
        if component.reference.is_empty() {
            return Err(PlacementError::invalid_component(
                "Component reference cannot be empty",
            ));
        }

        if component.width <= 0.0 || component.height <= 0.0 {
            return Err(PlacementError::invalid_component(format!(
                "Component {} has invalid dimensions: {}x{}",
                component.reference, component.width, component.height
            )));
        }

        if component.footprint.is_empty() {
            return Err(PlacementError::invalid_component(format!(
                "Component {} has empty footprint",
                component.reference
            )));
        }

        Ok(())
    }

    /// Validate a connection
    pub fn validate_connection(connection: &Connection) -> PlacementResult<()> {
        if connection.ref1.is_empty() || connection.ref2.is_empty() {
            return Err(PlacementError::invalid_connection(
                &connection.ref1,
                &connection.ref2,
            ));
        }

        if connection.ref1 == connection.ref2 {
            return Err(PlacementError::invalid_connection(
                &connection.ref1,
                &connection.ref2,
            ));
        }

        Ok(())
    }

    /// Validate placement configuration
    pub fn validate_config(config: &PlacementConfig) -> PlacementResult<()> {
        if config.component_spacing <= 0.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Component spacing must be positive, got {}",
                config.component_spacing
            )));
        }

        if config.attraction_strength < 0.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Attraction strength must be non-negative, got {}",
                config.attraction_strength
            )));
        }

        if config.repulsion_strength < 0.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Repulsion strength must be non-negative, got {}",
                config.repulsion_strength
            )));
        }

        if config.damping <= 0.0 || config.damping > 1.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Damping must be in (0, 1], got {}",
                config.damping
            )));
        }

        if config.cooling_rate <= 0.0 || config.cooling_rate > 1.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Cooling rate must be in (0, 1], got {}",
                config.cooling_rate
            )));
        }

        if config.iterations_per_level == 0 {
            return Err(PlacementError::invalid_configuration(
                "Iterations per level must be positive".to_string(),
            ));
        }

        Ok(())
    }

    /// Validate board dimensions
    pub fn validate_board_dimensions(width: f64, height: f64) -> PlacementResult<()> {
        if width <= 0.0 || height <= 0.0 {
            return Err(PlacementError::invalid_board_dimensions(width, height));
        }

        if width > 1000.0 || height > 1000.0 {
            return Err(PlacementError::invalid_configuration(format!(
                "Board dimensions too large: {}x{}mm",
                width, height
            )));
        }

        Ok(())
    }

    /// Validate a list of components
    pub fn validate_components(components: &[Component]) -> PlacementResult<()> {
        if components.is_empty() {
            return Ok(());
        }

        // Check for duplicate references
        let mut references = std::collections::HashSet::new();
        for component in components {
            validate_component(component)?;

            if !references.insert(&component.reference) {
                return Err(PlacementError::invalid_component(format!(
                    "Duplicate component reference: {}",
                    component.reference
                )));
            }
        }

        Ok(())
    }

    /// Validate a list of connections
    pub fn validate_connections(
        connections: &[Connection],
        components: &[Component],
    ) -> PlacementResult<()> {
        let component_refs: std::collections::HashSet<_> =
            components.iter().map(|c| &c.reference).collect();

        for connection in connections {
            validate_connection(connection)?;

            // Check that referenced components exist
            if !component_refs.contains(&connection.ref1) {
                return Err(PlacementError::component_not_found(&connection.ref1));
            }

            if !component_refs.contains(&connection.ref2) {
                return Err(PlacementError::component_not_found(&connection.ref2));
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{Component, Connection, PlacementConfig, Point};

    #[test]
    fn test_valid_component() {
        let component = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_size(2.0, 1.0);

        assert!(validation::validate_component(&component).is_ok());
    }

    #[test]
    fn test_invalid_component_empty_reference() {
        let mut component =
            Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string());
        component.reference = String::new();

        assert!(validation::validate_component(&component).is_err());
    }

    #[test]
    fn test_invalid_component_zero_dimensions() {
        let component = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_size(0.0, 1.0);

        assert!(validation::validate_component(&component).is_err());
    }

    #[test]
    fn test_valid_connection() {
        let connection = Connection::new("R1".to_string(), "R2".to_string());
        assert!(validation::validate_connection(&connection).is_ok());
    }

    #[test]
    fn test_invalid_connection_same_component() {
        let connection = Connection::new("R1".to_string(), "R1".to_string());
        assert!(validation::validate_connection(&connection).is_err());
    }

    #[test]
    fn test_valid_config() {
        let config = PlacementConfig::default();
        assert!(validation::validate_config(&config).is_ok());
    }

    #[test]
    fn test_invalid_config_negative_spacing() {
        let mut config = PlacementConfig::default();
        config.component_spacing = -1.0;
        assert!(validation::validate_config(&config).is_err());
    }

    #[test]
    fn test_valid_board_dimensions() {
        assert!(validation::validate_board_dimensions(100.0, 80.0).is_ok());
    }

    #[test]
    fn test_invalid_board_dimensions() {
        assert!(validation::validate_board_dimensions(-10.0, 80.0).is_err());
        assert!(validation::validate_board_dimensions(100.0, 0.0).is_err());
        assert!(validation::validate_board_dimensions(2000.0, 80.0).is_err());
    }
}
