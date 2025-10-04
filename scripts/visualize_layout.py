#!/usr/bin/env python3
"""
Visualize component placement from intermediate JSON layout file.

Usage:
    python visualize_layout.py <layout.json> [output.png]
"""

import sys
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def visualize_layout(json_path: Path, output_path: Path = None):
    """
    Visualize component bounding boxes from layout JSON.

    Args:
        json_path: Path to layout JSON file
        output_path: Optional path to save figure
    """
    # Load layout data
    with open(json_path, 'r') as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    components = data.get("components", [])

    # Determine sheet size (default A4: 210x297mm)
    sheet_width = 210.0
    sheet_height = 297.0

    # Create figure with KiCad orientation (origin top-left, Y increases downward)
    fig, ax = plt.subplots(figsize=(12, 16))

    # Set axis limits to match sheet
    ax.set_xlim(0, sheet_width)
    ax.set_ylim(0, sheet_height)

    # Flip Y-axis to match KiCad (top-left origin, Y down)
    ax.invert_yaxis()

    # Draw sheet boundary
    sheet_rect = patches.Rectangle(
        (0, 0), sheet_width, sheet_height,
        linewidth=2, edgecolor='black', facecolor='white', zorder=0
    )
    ax.add_patch(sheet_rect)

    # Draw each component bounding box
    for comp in components:
        ref = comp["ref"]
        bbox = comp["bbox"]

        x1 = bbox["x1"]
        y1 = bbox["y1"]
        width = bbox["width"]
        height = bbox["height"]

        # Draw rectangle
        rect = patches.Rectangle(
            (x1, y1), width, height,
            linewidth=1.5, edgecolor='blue', facecolor='lightblue', alpha=0.3, zorder=1
        )
        ax.add_patch(rect)

        # Add label in center
        center_x = x1 + width / 2
        center_y = y1 + height / 2
        ax.text(
            center_x, center_y, ref,
            ha='center', va='center',
            fontsize=10, fontweight='bold', zorder=2
        )

        # Add dimensions as small text
        ax.text(
            center_x, center_y + height/4, f"{width:.1f}×{height:.1f}mm",
            ha='center', va='center',
            fontsize=7, color='gray', zorder=2
        )

    # Set labels and title
    ax.set_xlabel('X (mm)', fontsize=12)
    ax.set_ylabel('Y (mm)', fontsize=12)
    ax.set_title(f'Schematic Component Layout - {metadata.get("component_count", len(components))} components', fontsize=14, fontweight='bold')

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add metadata text
    info_text = f"Sheet: {sheet_width}×{sheet_height}mm (A4)\n"
    info_text += f"Algorithm: {metadata.get('algorithm', 'unknown')}\n"
    info_text += f"Spacing: {metadata.get('spacing_mm', 0)}mm\n"
    info_text += f"Margin: {metadata.get('margin_mm', 0)}mm"

    ax.text(
        0.02, 0.98, info_text,
        transform=ax.transAxes,
        fontsize=9, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    plt.tight_layout()

    # Save or show
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✅ Visualization saved to: {output_path}")
    else:
        plt.show()


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_layout.py <layout.json> [output.png]")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)

    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else None

    print(f"📊 Visualizing layout from: {json_path}")
    visualize_layout(json_path, output_path)


if __name__ == "__main__":
    main()
