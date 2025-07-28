#!/usr/bin/env python3
"""
Visualize the force-directed placement results.

This script creates a visual comparison of the PCB layout before and after
applying the force-directed placement algorithm.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

from circuit_synth.kicad_api.pcb import PCBBoard


def plot_pcb(pcb: PCBBoard, ax, title: str):
    """Plot a PCB layout with components and connections."""
    # Get board outline
    outline = pcb.pcb_data.get("board_outline", {})
    if "rect" in outline:
        rect = outline["rect"]
        board_rect = Rectangle(
            (rect["x"], rect["y"]),
            rect["width"],
            rect["height"],
            fill=False,
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(board_rect)

        # Set axis limits with margin
        margin = 10
        ax.set_xlim(rect["x"] - margin, rect["x"] + rect["width"] + margin)
        ax.set_ylim(rect["y"] - margin, rect["y"] + rect["height"] + margin)

    # Plot components
    component_positions = {}
    for footprint in pcb.footprints:
        x = footprint.position.x
        y = footprint.position.y
        ref = footprint.reference

        # Store position for connections
        component_positions[ref] = (x, y)

        # Determine component color based on type
        if ref.startswith("U"):
            color = "lightblue"
            size = 8
        elif ref.startswith("R"):
            color = "lightcoral"
            size = 3
        elif ref.startswith("C"):
            color = "lightgreen"
            size = 3
        elif ref.startswith("J"):
            color = "yellow"
            size = 5
        else:
            color = "lightgray"
            size = 4

        # Draw component as a fancy box
        box = FancyBboxPatch(
            (x - size / 2, y - size / 2),
            size,
            size,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="black",
            linewidth=1,
        )
        ax.add_patch(box)

        # Add reference text
        ax.text(x, y, ref, ha="center", va="center", fontsize=8, weight="bold")

    # Plot connections (ratsnest)
    ratsnest = pcb.get_ratsnest()
    for connection in ratsnest:
        ref1 = connection["from_ref"]
        ref2 = connection["to_ref"]

        if ref1 in component_positions and ref2 in component_positions:
            x1, y1 = component_positions[ref1]
            x2, y2 = component_positions[ref2]

            # Draw connection line
            ax.plot([x1, x2], [y1, y2], "b-", alpha=0.3, linewidth=0.5)

    # Set title and labels
    ax.set_title(title, fontsize=14, weight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    # Add statistics
    bbox = pcb.get_placement_bbox()
    if bbox:
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        stats_text = f"Area: {width:.1f} x {height:.1f} mm"
        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )


def main():
    """Run the visualization."""
    print("Force-Directed Placement Visualization")
    print("=" * 50)

    # Load PCB files
    try:
        pcb_before = PCBBoard()
        pcb_before.load("force_directed_before.kicad_pcb")
        print("✓ Loaded 'before' PCB")

        pcb_after = PCBBoard()
        pcb_after.load("force_directed_after.kicad_pcb")
        print("✓ Loaded 'after' PCB")
    except FileNotFoundError:
        print("\n❌ Error: PCB files not found!")
        print(
            "   Please run 'force_directed_simple_demo.py' first to generate the files."
        )
        return

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Plot before and after
    plot_pcb(pcb_before, ax1, "Before: Initial Placement")
    plot_pcb(pcb_after, ax2, "After: Force-Directed Placement")

    # Add main title
    fig.suptitle("Force-Directed PCB Component Placement", fontsize=16, weight="bold")

    # Adjust layout and show
    plt.tight_layout()

    # Save the visualization
    output_file = "force_directed_comparison.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\n✓ Saved visualization to: {output_file}")

    # Show the plot
    plt.show()


if __name__ == "__main__":
    main()
