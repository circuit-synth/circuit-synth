//! Core types for force-directed placement algorithm

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

/// 2D point representing component position
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    pub fn distance_to(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    pub fn distance_squared_to(&self, other: &Point) -> f64 {
        (self.x - other.x).powi(2) + (self.y - other.y).powi(2)
    }
}

impl std::ops::Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

impl std::ops::Sub for Point {
    type Output = Point;

    fn sub(self, other: Point) -> Point {
        Point {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

impl std::ops::Mul<f64> for Point {
    type Output = Point;

    fn mul(self, scalar: f64) -> Point {
        Point {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

/// 2D force vector
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Force {
    pub fx: f64,
    pub fy: f64,
}

impl Force {
    pub fn new(fx: f64, fy: f64) -> Self {
        Self { fx, fy }
    }

    pub fn zero() -> Self {
        Self { fx: 0.0, fy: 0.0 }
    }

    pub fn magnitude(&self) -> f64 {
        (self.fx * self.fx + self.fy * self.fy).sqrt()
    }

    pub fn normalize(&self) -> Self {
        let mag = self.magnitude();
        if mag > 0.0 {
            Self {
                fx: self.fx / mag,
                fy: self.fy / mag,
            }
        } else {
            Self::zero()
        }
    }

    pub fn limit(&self, max_magnitude: f64) -> Self {
        let mag = self.magnitude();
        if mag > max_magnitude {
            let scale = max_magnitude / mag;
            Self {
                fx: self.fx * scale,
                fy: self.fy * scale,
            }
        } else {
            *self
        }
    }
}

impl std::ops::Add for Force {
    type Output = Force;

    fn add(self, other: Force) -> Force {
        Force {
            fx: self.fx + other.fx,
            fy: self.fy + other.fy,
        }
    }
}

impl std::ops::AddAssign for Force {
    fn add_assign(&mut self, other: Force) {
        self.fx += other.fx;
        self.fy += other.fy;
    }
}

impl std::ops::Mul<f64> for Force {
    type Output = Force;

    fn mul(self, scalar: f64) -> Force {
        Force {
            fx: self.fx * scalar,
            fy: self.fy * scalar,
        }
    }
}

/// Component representation for placement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub reference: String,
    pub position: Point,
    pub rotation: f64,
    pub footprint: String,
    pub value: String,
    pub path: String,
    pub width: f64,
    pub height: f64,
}

impl Component {
    pub fn new(reference: String, footprint: String, value: String) -> Self {
        Self {
            reference,
            position: Point::new(0.0, 0.0),
            rotation: 0.0,
            footprint,
            value,
            path: String::new(),
            width: 2.0,  // Default component size
            height: 2.0,
        }
    }

    pub fn with_position(mut self, position: Point) -> Self {
        self.position = position;
        self
    }

    pub fn with_size(mut self, width: f64, height: f64) -> Self {
        self.width = width;
        self.height = height;
        self
    }

    pub fn with_path(mut self, path: String) -> Self {
        self.path = path;
        self
    }

    pub fn bounding_box(&self) -> BoundingBox {
        let half_width = self.width / 2.0;
        let half_height = self.height / 2.0;
        
        BoundingBox {
            min_x: self.position.x - half_width,
            min_y: self.position.y - half_height,
            max_x: self.position.x + half_width,
            max_y: self.position.y + half_height,
        }
    }
}

/// Bounding box for collision detection
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min_x: f64,
    pub min_y: f64,
    pub max_x: f64,
    pub max_y: f64,
}

impl BoundingBox {
    pub fn new(min_x: f64, min_y: f64, max_x: f64, max_y: f64) -> Self {
        Self { min_x, min_y, max_x, max_y }
    }

    pub fn width(&self) -> f64 {
        self.max_x - self.min_x
    }

    pub fn height(&self) -> f64 {
        self.max_y - self.min_y
    }

    pub fn center(&self) -> Point {
        Point::new(
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0,
        )
    }

    pub fn intersects(&self, other: &BoundingBox) -> bool {
        self.min_x < other.max_x
            && self.max_x > other.min_x
            && self.min_y < other.max_y
            && self.max_y > other.min_y
    }

    pub fn contains_point(&self, point: &Point) -> bool {
        point.x >= self.min_x
            && point.x <= self.max_x
            && point.y >= self.min_y
            && point.y <= self.max_y
    }

    pub fn expand(&self, margin: f64) -> Self {
        Self {
            min_x: self.min_x - margin,
            min_y: self.min_y - margin,
            max_x: self.max_x + margin,
            max_y: self.max_y + margin,
        }
    }
}

/// Connection between two components
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Connection {
    pub ref1: String,
    pub ref2: String,
    pub net_name: String,
    pub is_critical: bool,
}

impl Connection {
    pub fn new(ref1: String, ref2: String) -> Self {
        Self {
            ref1,
            ref2,
            net_name: String::new(),
            is_critical: false,
        }
    }

    pub fn with_net(mut self, net_name: String) -> Self {
        self.net_name = net_name;
        self
    }

    pub fn with_critical(mut self, is_critical: bool) -> Self {
        self.is_critical = is_critical;
        self
    }

    pub fn contains_ref(&self, reference: &str) -> bool {
        self.ref1 == reference || self.ref2 == reference
    }

    pub fn other_ref(&self, reference: &str) -> Option<&str> {
        if self.ref1 == reference {
            Some(&self.ref2)
        } else if self.ref2 == reference {
            Some(&self.ref1)
        } else {
            None
        }
    }
}

/// Subcircuit group for hierarchical placement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubcircuitGroup {
    pub path: String,
    pub components: Vec<String>,
    pub center: Point,
    pub bounding_box: BoundingBox,
    pub connections_to_other_groups: HashMap<String, usize>,
}

impl SubcircuitGroup {
    pub fn new(path: String) -> Self {
        Self {
            path,
            components: Vec::new(),
            center: Point::new(0.0, 0.0),
            bounding_box: BoundingBox::new(0.0, 0.0, 0.0, 0.0),
            connections_to_other_groups: HashMap::new(),
        }
    }

    pub fn add_component(&mut self, reference: String) {
        self.components.push(reference);
    }

    pub fn update_properties(&mut self, component_positions: &HashMap<String, Point>) {
        if self.components.is_empty() {
            return;
        }

        // Calculate center
        let mut sum_x = 0.0;
        let mut sum_y = 0.0;
        let mut count = 0;

        for comp_ref in &self.components {
            if let Some(pos) = component_positions.get(comp_ref) {
                sum_x += pos.x;
                sum_y += pos.y;
                count += 1;
            }
        }

        if count > 0 {
            self.center = Point::new(sum_x / count as f64, sum_y / count as f64);
        }

        // Calculate bounding box
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;

        for comp_ref in &self.components {
            if let Some(pos) = component_positions.get(comp_ref) {
                min_x = min_x.min(pos.x);
                min_y = min_y.min(pos.y);
                max_x = max_x.max(pos.x);
                max_y = max_y.max(pos.y);
            }
        }

        if min_x != f64::INFINITY {
            let margin = 5.0; // Add some margin
            self.bounding_box = BoundingBox::new(
                min_x - margin,
                min_y - margin,
                max_x + margin,
                max_y + margin,
            );
        }
    }
}

/// Configuration for force-directed placement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlacementConfig {
    pub component_spacing: f64,
    pub attraction_strength: f64,
    pub repulsion_strength: f64,
    pub iterations_per_level: usize,
    pub damping: f64,
    pub initial_temperature: f64,
    pub cooling_rate: f64,
    pub enable_rotation: bool,
    pub internal_force_multiplier: f64,
    pub convergence_threshold: f64,
    pub max_move_distance: f64,
}

impl Default for PlacementConfig {
    fn default() -> Self {
        Self {
            component_spacing: 2.0,
            attraction_strength: 1.5,
            repulsion_strength: 50.0,
            iterations_per_level: 100,
            damping: 0.8,
            initial_temperature: 10.0,
            cooling_rate: 0.95,
            enable_rotation: true,
            internal_force_multiplier: 2.0,
            convergence_threshold: 1.0,
            max_move_distance: 5.0,
        }
    }
}

/// Result of placement operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlacementResult {
    pub positions: HashMap<String, Point>,
    pub rotations: HashMap<String, f64>,
    pub iterations_used: usize,
    pub final_energy: f64,
    pub convergence_achieved: bool,
    pub collision_count: usize,
}

impl PlacementResult {
    pub fn new() -> Self {
        Self {
            positions: HashMap::new(),
            rotations: HashMap::new(),
            iterations_used: 0,
            final_energy: 0.0,
            convergence_achieved: false,
            collision_count: 0,
        }
    }
}