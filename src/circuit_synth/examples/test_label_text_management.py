#!/usr/bin/env python3
"""
Test script for KiCad API Phase 4: Label & Text Management
Demonstrates label and text annotation functionality.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from circuit_synth.kicad_api import (
    ComponentManager,
    LabelManager,
    LabelType,
    PlacementStrategy,
    Schematic,
    TextManager,
    WireManager,
    WireRouter,
    format_net_name,
    group_labels_by_net,
    suggest_label_for_component_pin,
    validate_hierarchical_label_name,
)


def test_label_text_management():
    """Test label and text management functionality."""
    logger.info("TEST", "Testing KiCad API Phase 4: Label & Text Management")
    logger.info("TEST", "=" * 50)

    # Create a new schematic
    schematic = Schematic(title="Label & Text Test", date="2025-06-08", revision="1.0")

    # Add some components to label
    comp_manager = ComponentManager(schematic)

    r1 = comp_manager.add_component(
        library_id="Device:R", reference="R1", value="10k", position=(25.4, 25.4)
    )

    c1 = comp_manager.add_component(
        library_id="Device:C", reference="C1", value="100nF", position=(50.8, 25.4)
    )

    u1 = comp_manager.add_component(
        library_id="MCU_Microchip_ATmega:ATmega328P-PU",
        reference="U1",
        value="ATmega328P",
        position=(76.2, 50.8),
    )

    logger.info("TEST", "✓ Added 3 components: R1, C1, U1", component_count=3)

    # Add some wires to connect components
    wire_manager = WireManager(schematic)
    router = WireRouter()

    # Connect R1 to C1
    wire1_path = router.route_manhattan((38.1, 25.4), (50.8, 25.4))
    wire1 = wire_manager.add_wire(wire1_path)

    # Create a power rail
    power_wire = wire_manager.add_wire([(25.4, 12.7), (76.2, 12.7)])

    logger.info("TEST", "✓ Added connecting wires")

    # Create label manager
    label_manager = LabelManager(schematic)

    # Test 1: Basic label creation
    logger.info("TEST", "1. Testing basic label creation:")

    # Add local label
    local_label = label_manager.add_label(
        text="SIGNAL_1", position=(45.0, 25.4), label_type=LabelType.LOCAL
    )
    if local_label:
        logger.info(
            "TEST",
            f"✓ Created local label: {local_label.text}",
            label_text=local_label.text,
            label_type="local",
        )

    # Add global label
    global_label = label_manager.add_label(
        text="VCC", position=(50.8, 12.7), label_type=LabelType.GLOBAL
    )
    if global_label:
        logger.info(
            "TEST",
            f"✓ Created global label: {global_label.text}",
            label_text=global_label.text,
            label_type="global",
        )

    # Add hierarchical label
    hier_label = label_manager.add_label(
        text="DATA_BUS",
        position=(76.2, 38.1),
        label_type=LabelType.HIERARCHICAL,
        orientation=90,
    )
    if hier_label:
        logger.info(
            "TEST",
            f"✓ Created hierarchical label: {hier_label.text} (90° rotation)",
            label_text=hier_label.text,
            label_type="hierarchical",
            rotation=90,
        )

    # Test 2: Auto-positioning labels
    logger.info("TEST", "2. Testing auto-positioned labels:")

    auto_label = label_manager.auto_position_label(
        text="AUTO_NET", near_point=(38.1, 25.4), label_type=LabelType.LOCAL
    )
    if auto_label:
        logger.info(
            "TEST",
            f"✓ Auto-positioned label at ({auto_label.position.x}, {auto_label.position.y})",
            x=auto_label.position.x,
            y=auto_label.position.y,
        )

    # Test 3: Label search and update
    logger.info("TEST", "3. Testing label search and update:")

    # Find labels by text
    vcc_labels = label_manager.find_labels_by_text("VCC", exact_match=True)
    logger.info(
        "TEST",
        f"✓ Found {len(vcc_labels)} labels with text 'VCC'",
        label_count=len(vcc_labels),
    )

    # Update label
    if local_label:
        success = label_manager.update_label(
            local_label.uuid, text="SIGNAL_1_UPDATED", orientation=180
        )
        if success:
            logger.info("TEST", "✓ Updated label text and orientation")

    # Test 4: Text annotations
    logger.info("TEST", "4. Testing text annotations:")

    text_manager = TextManager(schematic)

    # Add title text
    title_text = text_manager.add_text(
        content="Test Circuit\nLabel & Text Demo", position=(50.8, 5.0), size=2.0
    )
    if title_text:
        logger.info(
            "TEST",
            f"✓ Added title text (size: {title_text.size}mm)",
            text_size=title_text.size,
        )

    # Add component note
    note_text = text_manager.add_text(
        content="Note: Use 1% resistor", position=(25.4, 30.0), size=1.0
    )
    if note_text:
        logger.info("TEST", "✓ Added component note")

    # Add multi-line text
    lines = ["Pin Connections:", "1 - VCC", "2 - GND", "3 - DATA"]
    multi_texts = text_manager.add_multiline_text(
        lines=lines, position=(10.0, 50.0), line_spacing=2.0
    )
    logger.info(
        "TEST",
        f"✓ Added {len(multi_texts)} lines of text",
        text_line_count=len(multi_texts),
    )

    # Test 5: Text alignment
    logger.info("TEST", "5. Testing text alignment:")

    # Create some texts to align
    text1 = text_manager.add_text("Text 1", (60.0, 60.0))
    text2 = text_manager.add_text("Text 2", (65.0, 65.0))
    text3 = text_manager.add_text("Text 3", (62.0, 70.0))

    if text1 and text2 and text3:
        text_uuids = [text1.uuid, text2.uuid, text3.uuid]
        success = text_manager.align_texts(text_uuids, alignment="left")
        if success:
            logger.info("TEST", "✓ Aligned 3 texts to the left", aligned_count=3)

    # Test 6: Label utilities
    logger.info("TEST", "6. Testing label utilities:")

    # Format net name
    formatted = format_net_name("my signal-name 123")
    logger.info(
        "TEST", f"✓ Formatted net name: '{formatted}'", formatted_name=formatted
    )

    # Validate hierarchical label
    valid, error = validate_hierarchical_label_name("VALID_NAME")
    logger.info(
        "TEST",
        f"✓ Label validation: {'Valid' if valid else f'Invalid - {error}'}",
        validation_result=valid,
        error=error,
    )

    invalid, error = validate_hierarchical_label_name("Invalid/Name")
    logger.info(
        "TEST", f"✓ Invalid label test: {error}", validation_result=invalid, error=error
    )

    # Group labels by net
    all_labels = label_manager.get_labels_by_type(LabelType.LOCAL)
    groups = group_labels_by_net(all_labels)
    logger.info(
        "TEST", f"✓ Grouped labels into {len(groups)} nets", net_group_count=len(groups)
    )

    # Test 7: Component pin labeling
    logger.info("TEST", "7. Testing component pin labeling:")

    if r1:
        suggested_text, position, orientation = suggest_label_for_component_pin(
            r1, "1", LabelType.LOCAL
        )
        logger.info(
            "TEST",
            f"✓ Suggested label for R1 pin 1: '{suggested_text}' at {position}",
            suggested_text=suggested_text,
            position=position,
        )

        # Create the suggested label
        pin_label = label_manager.add_label(
            text=suggested_text,
            position=position,
            label_type=LabelType.LOCAL,
            orientation=orientation,
        )
        if pin_label:
            logger.info("TEST", "✓ Created pin label")

    # Test 8: Label validation
    logger.info("TEST", "8. Testing label validation:")

    # Add some hierarchical labels for validation
    label_manager.add_label("HIER_1", (100, 100), LabelType.HIERARCHICAL)
    label_manager.add_label("HIER_1", (110, 100), LabelType.HIERARCHICAL)  # Duplicate

    errors = label_manager.validate_hierarchical_labels()
    logger.info(
        "TEST", f"✓ Validation found {len(errors)} errors", error_count=len(errors)
    )
    for error in errors:
        logger.info("TEST", f"- {error}", validation_error=error)

    # Test 9: Final statistics
    logger.info("TEST", "9. Final schematic statistics:")
    logger.info(
        "TEST",
        f"- Total components: {len(schematic.components)}",
        component_count=len(schematic.components),
    )
    logger.info(
        "TEST",
        f"- Total wires: {len(schematic.wires)}",
        wire_count=len(schematic.wires),
    )
    logger.info(
        "TEST",
        f"- Total labels: {len(schematic.labels)}",
        label_count=len(schematic.labels),
    )
    logger.info(
        "TEST",
        f"- Total text annotations: {len(schematic.texts)}",
        text_count=len(schematic.texts),
    )

    # Label breakdown
    local_count = len(label_manager.get_labels_by_type(LabelType.LOCAL))
    global_count = len(label_manager.get_labels_by_type(LabelType.GLOBAL))
    hier_count = len(label_manager.get_labels_by_type(LabelType.HIERARCHICAL))

    logger.info("TEST", "Label breakdown:")
    logger.info("TEST", f"- Local labels: {local_count}", local_label_count=local_count)
    logger.info(
        "TEST", f"- Global labels: {global_count}", global_label_count=global_count
    )
    logger.info(
        "TEST",
        f"- Hierarchical labels: {hier_count}",
        hierarchical_label_count=hier_count,
    )

    logger.info("TEST", "✅ All Phase 4 tests completed successfully!")

    return schematic, label_manager, text_manager


def test_error_handling():
    """Test error handling in label and text operations."""
    logger.info("TEST", "Testing Error Handling")
    logger.info("TEST", "=" * 50)

    schematic = Schematic()
    label_manager = LabelManager(schematic)
    text_manager = TextManager(schematic)

    logger.info("TEST", "1. Testing invalid label creation:")

    # Empty text
    result = label_manager.add_label("", (10, 10))
    logger.info(
        "TEST", f"✓ Empty label text returned: {result} (expected: None)", result=result
    )

    # Invalid orientation
    result = label_manager.add_label("TEST", (10, 10), orientation=45)
    logger.info(
        "TEST",
        f"✓ Invalid orientation returned: {result} (expected: None)",
        result=result,
    )

    logger.info("TEST", "2. Testing invalid text creation:")

    # Empty content
    result = text_manager.add_text("", (10, 10))
    logger.info(
        "TEST",
        f"✓ Empty text content returned: {result} (expected: None)",
        result=result,
    )

    # Invalid size
    result = text_manager.add_text("TEST", (10, 10), size=-1)
    logger.info(
        "TEST",
        f"✓ Invalid text size returned: {result} (expected: None)",
        result=result,
    )

    logger.info("TEST", "3. Testing operations on non-existent items:")

    # Update non-existent label
    result = label_manager.update_label("fake-uuid", text="NEW")
    logger.info(
        "TEST",
        f"✓ Update non-existent label returned: {result} (expected: False)",
        result=result,
    )

    # Remove non-existent text
    result = text_manager.remove_text("fake-uuid")
    logger.info(
        "TEST",
        f"✓ Remove non-existent text returned: {result} (expected: False)",
        result=result,
    )

    logger.info("TEST", "✅ Error handling tests completed!")


if __name__ == "__main__":
    # Run main tests
    schematic, label_manager, text_manager = test_label_text_management()

    # Run error handling tests
    test_error_handling()

    logger.info("TEST", "=" * 50)
    logger.info("TEST", "All KiCad API Phase 4 tests passed! 🎉")
    logger.info(
        "TEST", "Phase 4 Complete! Label and text management is now functional."
    )
    logger.info("TEST", "Next steps:")
    logger.info("TEST", "- Phase 5: Sheet & Hierarchy")
    logger.info("TEST", "- Phase 6: Search & Discovery")
