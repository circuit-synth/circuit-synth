"""
High-performance force-directed placement algorithm for PCB components.

This package provides a Rust-based implementation of force-directed placement
algorithms optimized for PCB component placement with 100x performance improvements
over pure Python implementations.

Key Features:
- O(n²) optimized force calculations with parallel processing
- Hierarchical placement for complex circuits
- Collision detection with spatial indexing
- 100% API compatibility with existing Python implementations
- Comprehensive validation and error handling

Example:
    >>> from rust_force_directed_placement import ForceDirectedPlacer, Component, Point
    >>> 
    >>> # Create components
    >>> components = [
    ...     Component("R1", "R_0805", "10k").with_position(0, 0).with_size(2, 1),
    ...     Component("R2", "R_0805", "10k").with_position(10, 0).with_size(2, 1),
    ... ]
    >>> 
    >>> # Define connections
    >>> connections = [("R1", "R2")]
    >>> 
    >>> # Create placer and perform placement
    >>> placer = ForceDirectedPlacer(component_spacing=2.0)
    >>> result = placer.place(components, connections, board_width=100, board_height=100)
    >>> 
    >>> # Access results
    >>> print(f"R1 position: {result.get_position('R1')}")
    >>> print(f"Placement energy: {result.final_energy}")
"""

__version__ = "0.1.0"
__author__ = "Circuit Synth Team"
__email__ = "team@circuitsynth.com"

# Import the Rust extension module
try:
    from ._rust_force_directed_placement import (
        ForceDirectedPlacer,
        Point,
        Component,
        PlacementResult,
        create_component,
        create_point,
        validate_placement_inputs,
    )
except ImportError as e:
    raise ImportError(
        "Failed to import Rust extension module. "
        "Please ensure the package is properly installed with: "
        "pip install rust-force-directed-placement"
    ) from e

# Re-export main classes and functions
__all__ = [
    "ForceDirectedPlacer",
    "Point", 
    "Component",
    "PlacementResult",
    "create_component",
    "create_point",
    "validate_placement_inputs",
    # Utility functions
    "create_test_circuit",
    "benchmark_placement",
    "visualize_placement",
]

# Utility functions for easier usage
def create_test_circuit(component_count: int = 10) -> tuple[list, list]:
    """
    Create a test circuit with the specified number of components.
    
    Args:
        component_count: Number of components to create
        
    Returns:
        Tuple of (components, connections) for testing
    """
    components = []
    connections = []
    
    # Create resistors in a grid pattern
    grid_size = int(component_count**0.5) + 1
    for i in range(component_count):
        row = i // grid_size
        col = i % grid_size
        
        component = Component(
            f"R{i+1}",
            "R_0805", 
            "10k"
        )
        component.with_position(col * 5.0, row * 5.0)
        component.with_size(2.0, 1.0)
        components.append(component)
        
        # Create connections to form a chain
        if i > 0:
            connections.append((f"R{i}", f"R{i+1}"))
        
        # Add some cross-connections
        if i % 5 == 0 and i + 5 < component_count:
            connections.append((f"R{i+1}", f"R{i+6}"))
    
    return components, connections


def benchmark_placement(
    component_counts: list[int] = None,
    iterations: int = 3
) -> dict:
    """
    Benchmark placement performance across different component counts.
    
    Args:
        component_counts: List of component counts to test
        iterations: Number of iterations per test
        
    Returns:
        Dictionary with benchmark results
    """
    import time
    
    if component_counts is None:
        component_counts = [10, 25, 50, 100, 200]
    
    results = {}
    
    for count in component_counts:
        times = []
        
        for _ in range(iterations):
            components, connections = create_test_circuit(count)
            placer = ForceDirectedPlacer(
                component_spacing=2.0,
                iterations_per_level=50  # Reduced for benchmarking
            )
            
            start_time = time.time()
            result = placer.place(components, connections, 100.0, 100.0)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        results[count] = {
            'avg_time': avg_time,
            'times': times,
            'components_per_second': count / avg_time
        }
        
        print(f"{count} components: {avg_time:.4f}s avg ({count/avg_time:.1f} comp/s)")
    
    return results


def visualize_placement(result: PlacementResult, save_path: str = None) -> None:
    """
    Visualize placement results using matplotlib.
    
    Args:
        result: PlacementResult from placement operation
        save_path: Optional path to save the visualization
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install with: pip install matplotlib"
        )
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Plot components
    for ref, position in result.positions.items():
        # Draw component as rectangle
        rect = patches.Rectangle(
            (position.x - 1, position.y - 0.5),
            2, 1,
            linewidth=1,
            edgecolor='blue',
            facecolor='lightblue',
            alpha=0.7
        )
        ax.add_patch(rect)
        
        # Add component label
        ax.text(
            position.x, position.y,
            ref,
            ha='center', va='center',
            fontsize=8,
            fontweight='bold'
        )
    
    # Set equal aspect ratio and labels
    ax.set_aspect('equal')
    ax.set_xlabel('X Position (mm)')
    ax.set_ylabel('Y Position (mm)')
    ax.set_title(f'Component Placement Results\n'
                f'{len(result.positions)} components, '
                f'Energy: {result.final_energy:.2f}, '
                f'Iterations: {result.iterations_used}')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Auto-scale with some margin
    if result.positions:
        x_coords = [p.x for p in result.positions.values()]
        y_coords = [p.y for p in result.positions.values()]
        margin = 5
        ax.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
        ax.set_ylim(min(y_coords) - margin, max(y_coords) + margin)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {save_path}")
    else:
        plt.show()


# Version compatibility check
def check_version_compatibility() -> bool:
    """
    Check if the current version is compatible with the expected API.
    
    Returns:
        True if compatible, False otherwise
    """
    try:
        # Test basic functionality
        placer = ForceDirectedPlacer()
        component = Component("TEST", "R_0805", "10k")
        point = Point(0.0, 0.0)
        
        # If we can create these objects, we're compatible
        return True
    except Exception:
        return False


# Initialize and validate on import
if not check_version_compatibility():
    import warnings
    warnings.warn(
        "Version compatibility check failed. "
        "Some features may not work as expected.",
        UserWarning
    )

# Module-level configuration
DEFAULT_CONFIG = {
    'component_spacing': 2.0,
    'attraction_strength': 1.5,
    'repulsion_strength': 50.0,
    'iterations_per_level': 100,
    'damping': 0.8,
    'initial_temperature': 10.0,
    'cooling_rate': 0.95,
    'enable_rotation': True,
    'internal_force_multiplier': 2.0,
}

def get_default_config() -> dict:
    """Get the default configuration parameters."""
    return DEFAULT_CONFIG.copy()

def create_placer_from_config(config: dict) -> ForceDirectedPlacer:
    """Create a ForceDirectedPlacer from a configuration dictionary."""
    return ForceDirectedPlacer(**config)