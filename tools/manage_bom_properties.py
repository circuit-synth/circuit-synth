#!/usr/bin/env python3
"""
BOM Property Management Script - Enhanced Version

Not just audit - also UPDATE, TRANSFORM, and MANAGE component properties!

Features:
  - Audit mode: Find missing properties (original functionality)
  - Update mode: Bulk property changes with pattern matching
  - Transform mode: Copy/rename properties
  - Regex support: Flexible matching on any field

Perfect for:
  - Migrating from MPN to PartNumber
  - Bulk updating part numbers by value/footprint
  - Cleaning up property naming inconsistencies
  - Adding manufacturer data in bulk

Usage:
    # Audit (find missing)
    python scripts/manage_bom_properties.py audit ~/designs --check PartNumber

    # Update (bulk changes)
    python scripts/manage_bom_properties.py update ~/designs \
      --match "value=10k,footprint=*0805*" \
      --set "PartNumber=RC0805FR-0710KL,Manufacturer=Yageo"

    # Transform (copy/rename properties)
    python scripts/manage_bom_properties.py transform ~/designs \
      --copy "MPN->PartNumber" \
      --only-if-empty

Author: circuit-synth
Date: 2025-11-18
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import csv
import fnmatch

# Add kicad-sch-api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


@dataclass
class ComponentMatch:
    """Component that matches search criteria."""
    schematic_path: Path
    component: object  # ksa.Component
    matched_fields: Dict[str, str]


class PropertyMatcher:
    """Match components based on criteria with regex/wildcard support."""

    @staticmethod
    def parse_criteria(criteria_str: str) -> Dict[str, str]:
        """
        Parse criteria string into dict.

        Examples:
            "value=10k,footprint=*0805*"
            "reference=R*,lib_id=Device:R"
            "PartNumber="  # Empty property
        """
        if not criteria_str:
            return {}

        criteria = {}
        for pair in criteria_str.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                criteria[key.strip()] = value.strip()

        return criteria

    @staticmethod
    def matches(component, criteria: Dict[str, str]) -> bool:
        """
        Check if component matches all criteria.

        Supports:
          - Exact match: "value=10k"
          - Wildcards: "footprint=*0805*"
          - Regex: "reference=R[0-9]+"
          - Empty check: "PartNumber=" (matches if empty)
        """
        for field, pattern in criteria.items():
            # Get field value from component
            if field == "properties":
                # Special case: check if component has any property
                component_value = str(component.properties)
            elif field in ["reference", "value", "footprint", "lib_id"]:
                component_value = getattr(component, field, "")
            else:
                # Assume it's a property
                component_value = component.get_property(field, "")

            component_value = str(component_value)

            # Empty check
            if pattern == "":
                if component_value != "":
                    return False
                continue

            # Wildcard match
            if '*' in pattern or '?' in pattern:
                if not fnmatch.fnmatch(component_value, pattern):
                    return False
                continue

            # Try regex match
            try:
                if not re.search(pattern, component_value):
                    return False
            except re.error:
                # Not valid regex, try exact match
                if component_value != pattern:
                    return False

        return True


def find_components(
    schematic_path: Path,
    criteria: Dict[str, str],
    exclude_dnp: bool = False
) -> List[ComponentMatch]:
    """Find components matching criteria in schematic."""
    matches = []

    try:
        sch = ksa.Schematic.load(str(schematic_path))

        for component in sch.components.all():
            if exclude_dnp and not component.in_bom:
                continue

            if PropertyMatcher.matches(component, criteria):
                matched_fields = {
                    "reference": component.reference,
                    "value": component.value,
                    "footprint": component.footprint or "",
                    "lib_id": component.lib_id,
                }
                matches.append(ComponentMatch(
                    schematic_path=schematic_path,
                    component=component,
                    matched_fields=matched_fields
                ))

    except Exception as e:
        print(f"ERROR loading {schematic_path}: {e}", file=sys.stderr)

    return matches


def update_properties(
    matches: List[ComponentMatch],
    property_updates: Dict[str, str],
    dry_run: bool = False
) -> int:
    """
    Update properties on matched components.

    Args:
        matches: Components to update
        property_updates: Properties to set (name -> value)
        dry_run: If True, don't actually save changes

    Returns:
        Number of components updated
    """
    # Group matches by schematic
    by_schematic = {}
    for match in matches:
        path = match.schematic_path
        if path not in by_schematic:
            by_schematic[path] = []
        by_schematic[path].append(match)

    updated_count = 0

    for sch_path, sch_matches in by_schematic.items():
        try:
            # Load schematic
            sch = ksa.Schematic.load(str(sch_path))

            # Update each matched component
            for match in sch_matches:
                component = match.component

                for prop_name, prop_value in property_updates.items():
                    if dry_run:
                        print(f"  Would set {component.reference}.{prop_name} = {prop_value}")
                    else:
                        component.set_property(prop_name, prop_value)
                        print(f"  Set {component.reference}.{prop_name} = {prop_value}")

                updated_count += 1

            # Save schematic
            if not dry_run:
                sch.save(str(sch_path))
                print(f"✓ Saved {sch_path.name}")

        except Exception as e:
            print(f"ERROR updating {sch_path}: {e}", file=sys.stderr)

    return updated_count


def transform_properties(
    matches: List[ComponentMatch],
    transformations: List[tuple],  # [(from_prop, to_prop), ...]
    only_if_empty: bool = False,
    dry_run: bool = False
) -> int:
    """
    Copy/rename properties on matched components.

    Args:
        matches: Components to transform
        transformations: List of (source_prop, dest_prop) tuples
        only_if_empty: Only copy if destination is empty
        dry_run: Don't actually save changes

    Returns:
        Number of components updated
    """
    by_schematic = {}
    for match in matches:
        path = match.schematic_path
        if path not in by_schematic:
            by_schematic[path] = []
        by_schematic[path].append(match)

    updated_count = 0

    for sch_path, sch_matches in by_schematic.items():
        try:
            sch = ksa.Schematic.load(str(sch_path))

            for match in sch_matches:
                component = match.component

                for from_prop, to_prop in transformations:
                    source_value = component.get_property(from_prop)
                    dest_value = component.get_property(to_prop)

                    if not source_value:
                        continue  # Nothing to copy

                    if only_if_empty and dest_value:
                        continue  # Destination already has value

                    if dry_run:
                        print(f"  Would copy {component.reference}.{from_prop} -> {to_prop} = {source_value}")
                    else:
                        component.set_property(to_prop, source_value)
                        print(f"  Copied {component.reference}.{from_prop} -> {to_prop} = {source_value}")

                    updated_count += 1

            if not dry_run:
                sch.save(str(sch_path))
                print(f"✓ Saved {sch_path.name}")

        except Exception as e:
            print(f"ERROR transforming {sch_path}: {e}", file=sys.stderr)

    return updated_count


# ========== AUDIT MODE FUNCTIONS ==========

@dataclass
class ComponentIssue:
    """Component with missing properties."""
    schematic: str
    reference: str
    value: str
    footprint: str
    lib_id: str
    missing_properties: List[str]
    existing_properties: Dict[str, str]


def audit_schematic(
    schematic_path: Path,
    required_properties: List[str],
    exclude_dnp: bool = False
) -> List[ComponentIssue]:
    """Audit single schematic for missing properties."""
    issues = []

    try:
        sch = ksa.Schematic.load(str(schematic_path))

        for component in sch.components.all():
            if exclude_dnp and not component.in_bom:
                continue

            # Check which required properties are missing
            missing = []
            for prop in required_properties:
                if not component.get_property(prop):
                    missing.append(prop)

            # If any properties missing, record the issue
            if missing:
                issues.append(ComponentIssue(
                    schematic=str(schematic_path),
                    reference=component.reference,
                    value=component.value,
                    footprint=component.footprint or "",
                    lib_id=component.lib_id,
                    missing_properties=missing,
                    existing_properties=dict(component.properties)
                ))

    except Exception as e:
        print(f"ERROR loading {schematic_path}: {e}", file=sys.stderr)

    return issues


def audit_directory(
    directory: Path,
    required_properties: List[str],
    recursive: bool = True,
    exclude_dnp: bool = False
) -> List[ComponentIssue]:
    """Scan directory for schematics and audit all."""
    all_issues = []

    # Find all .kicad_sch files
    if recursive:
        schematic_files = list(directory.rglob("*.kicad_sch"))
    else:
        schematic_files = list(directory.glob("*.kicad_sch"))

    print(f"Found {len(schematic_files)} schematic(s) to audit...")

    # Audit each schematic
    for sch_file in schematic_files:
        print(f"  Auditing: {sch_file.name}...", end=" ")
        issues = audit_schematic(sch_file, required_properties, exclude_dnp)
        all_issues.extend(issues)
        print(f"{len(issues)} issue(s)")

    return all_issues


def generate_csv_report(issues: List[ComponentIssue], output_path: Path):
    """Generate CSV report from audit results."""
    if not issues:
        print("No issues found! All components have required properties.")
        return

    # Collect all property names that exist across components
    all_property_names = set()
    for issue in issues:
        all_property_names.update(issue.existing_properties.keys())

    # Create CSV with dynamic columns
    fieldnames = [
        "Schematic",
        "Reference",
        "Value",
        "Footprint",
        "LibID",
        "MissingProperties",
    ]

    # Add common properties as columns
    common_props = ["Tolerance", "Manufacturer", "MPN", "Datasheet", "Description"]
    for prop in common_props:
        if prop in all_property_names:
            fieldnames.append(prop)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for issue in issues:
            row = {
                "Schematic": issue.schematic,
                "Reference": issue.reference,
                "Value": issue.value,
                "Footprint": issue.footprint,
                "LibID": issue.lib_id,
                "MissingProperties": ", ".join(issue.missing_properties),
            }

            # Add existing properties
            for prop in common_props:
                if prop in fieldnames:
                    prop_value = issue.existing_properties.get(prop, "")
                    if isinstance(prop_value, dict):
                        prop_value = prop_value.get('value', str(prop_value))
                    row[prop] = prop_value

            writer.writerow(row)

    print(f"\nReport written to: {output_path}")


def print_summary(issues: List[ComponentIssue], total_schematics: int):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("BOM Property Audit Summary")
    print("="*60)
    print(f"Schematics scanned: {total_schematics}")
    print(f"Components with missing properties: {len(issues)}")

    if issues:
        # Count by missing property
        property_counts = {}
        for issue in issues:
            for prop in issue.missing_properties:
                property_counts[prop] = property_counts.get(prop, 0) + 1

        print("\nMissing property breakdown:")
        for prop, count in sorted(property_counts.items()):
            print(f"  {prop}: {count} components")

        # Show a few examples
        print("\nExample components needing updates:")
        for issue in issues[:5]:
            print(f"  {issue.reference} ({issue.value}) - missing: {', '.join(issue.missing_properties)}")

        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")

    print("="*60 + "\n")


# ========== COMMAND HANDLERS ==========

def cmd_audit(args):
    """Audit mode: Find components missing properties."""
    issues = audit_directory(
        directory=args.directory,
        required_properties=args.check,
        recursive=not args.no_recursive,
        exclude_dnp=args.exclude_dnp
    )

    if not args.no_recursive:
        total_schematics = len(list(args.directory.rglob("*.kicad_sch")))
    else:
        total_schematics = len(list(args.directory.glob("*.kicad_sch")))

    print_summary(issues, total_schematics)

    if issues and args.output:
        generate_csv_report(issues, args.output)


def cmd_update(args):
    """Update mode: Bulk property changes."""
    # Parse match criteria
    criteria = PropertyMatcher.parse_criteria(args.match)
    if not criteria:
        print("ERROR: Must specify --match criteria", file=sys.stderr)
        sys.exit(1)

    # Parse property updates
    updates = PropertyMatcher.parse_criteria(args.set)
    if not updates:
        print("ERROR: Must specify --set properties", file=sys.stderr)
        sys.exit(1)

    print(f"\nBOM Property Update")
    print(f"Directory: {args.directory}")
    print(f"Match criteria: {criteria}")
    print(f"Property updates: {updates}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Find matching components
    print("Finding matching components...")
    if not args.no_recursive:
        schematic_files = list(args.directory.rglob("*.kicad_sch"))
    else:
        schematic_files = list(args.directory.glob("*.kicad_sch"))

    all_matches = []
    for sch_file in schematic_files:
        matches = find_components(sch_file, criteria, args.exclude_dnp)
        all_matches.extend(matches)

    print(f"Found {len(all_matches)} matching component(s)")

    if not all_matches:
        print("No components match criteria.")
        return

    # Show examples
    print("\nExample matches:")
    for match in all_matches[:5]:
        print(f"  {match.matched_fields['reference']} ({match.matched_fields['value']})")
    if len(all_matches) > 5:
        print(f"  ... and {len(all_matches) - 5} more")

    # Confirm before updating
    if not args.dry_run and not args.yes:
        response = input(f"\nUpdate {len(all_matches)} components? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    print()

    # Perform updates
    updated = update_properties(all_matches, updates, dry_run=args.dry_run)

    print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated} component(s)")


def cmd_transform(args):
    """Transform mode: Copy/rename properties."""
    # Parse transformations
    transformations = []
    for trans in args.copy:
        if '->' not in trans:
            print(f"ERROR: Invalid transformation '{trans}'. Expected format: 'SourceProp->DestProp'", file=sys.stderr)
            sys.exit(1)
        from_prop, to_prop = trans.split('->', 1)
        transformations.append((from_prop.strip(), to_prop.strip()))

    if not transformations:
        print("ERROR: Must specify --copy transformations", file=sys.stderr)
        sys.exit(1)

    # Parse match criteria (optional)
    criteria = PropertyMatcher.parse_criteria(args.match) if args.match else {}

    print(f"\nBOM Property Transform")
    print(f"Directory: {args.directory}")
    print(f"Transformations: {transformations}")
    if criteria:
        print(f"Match criteria: {criteria}")
    print(f"Only if empty: {args.only_if_empty}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Find matching components
    print("Finding components...")
    if not args.no_recursive:
        schematic_files = list(args.directory.rglob("*.kicad_sch"))
    else:
        schematic_files = list(args.directory.glob("*.kicad_sch"))

    all_matches = []
    for sch_file in schematic_files:
        matches = find_components(sch_file, criteria or {}, args.exclude_dnp)
        all_matches.extend(matches)

    print(f"Found {len(all_matches)} component(s)")

    if not all_matches:
        print("No components found.")
        return

    # Confirm before transforming
    if not args.dry_run and not args.yes:
        response = input(f"\nTransform {len(all_matches)} components? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    print()

    # Perform transformations
    updated = transform_properties(all_matches, transformations, args.only_if_empty, dry_run=args.dry_run)

    print(f"\n{'Would transform' if args.dry_run else 'Transformed'} {updated} component(s)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage BOM properties in KiCad schematics",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Find missing properties')
    audit_parser.add_argument('directory', type=Path, help='Directory to scan')
    audit_parser.add_argument('--check', nargs='+', default=['PartNumber'], help='Properties to check for')
    audit_parser.add_argument('--output', type=Path, help='Output CSV file')
    audit_parser.add_argument('--no-recursive', action='store_true', help="Don't scan subdirectories")
    audit_parser.add_argument('--exclude-dnp', action='store_true', help='Exclude DNP components')

    # Update command
    update_parser = subparsers.add_parser('update', help='Bulk property updates')
    update_parser.add_argument('directory', type=Path, help='Directory to scan')
    update_parser.add_argument('--match', required=True, help='Match criteria (value=10k,footprint=*0805*)')
    update_parser.add_argument('--set', required=True, help='Properties to set (PartNumber=XXX,Manufacturer=YYY)')
    update_parser.add_argument('--no-recursive', action='store_true', help="Don't scan subdirectories")
    update_parser.add_argument('--exclude-dnp', action='store_true', help='Exclude DNP components')
    update_parser.add_argument('--dry-run', action='store_true', help="Show what would be done without changing files")
    update_parser.add_argument('--yes', action='store_true', help="Don't ask for confirmation")

    # Transform command
    transform_parser = subparsers.add_parser('transform', help='Copy/rename properties')
    transform_parser.add_argument('directory', type=Path, help='Directory to scan')
    transform_parser.add_argument('--copy', nargs='+', required=True, help='Copy properties (MPN->PartNumber)')
    transform_parser.add_argument('--match', help='Optional match criteria')
    transform_parser.add_argument('--only-if-empty', action='store_true', help='Only copy if destination is empty')
    transform_parser.add_argument('--no-recursive', action='store_true', help="Don't scan subdirectories")
    transform_parser.add_argument('--exclude-dnp', action='store_true', help='Exclude DNP components')
    transform_parser.add_argument('--dry-run', action='store_true', help="Show what would be done")
    transform_parser.add_argument('--yes', action='store_true', help="Don't ask for confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Validate directory
    if not args.directory.exists():
        print(f"ERROR: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    # Run command
    if args.command == 'audit':
        cmd_audit(args)
    elif args.command == 'update':
        cmd_update(args)
    elif args.command == 'transform':
        cmd_transform(args)


if __name__ == "__main__":
    main()
