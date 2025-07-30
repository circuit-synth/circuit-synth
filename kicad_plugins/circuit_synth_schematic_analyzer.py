#!/usr/bin/env python3
"""
Circuit-Synth Schematic Analyzer

Standalone tool for analyzing KiCad schematic files since eeschema doesn't 
support ActionPlugins like pcbnew does.

Usage:
    python circuit_synth_schematic_analyzer.py <schematic_file.kicad_sch>
    python circuit_synth_schematic_analyzer.py --project <project_directory>
"""

import argparse
import json
import sys
from pathlib import Path

# Add the plugin directory to path
script_dir = Path(__file__).parent
plugin_dir = script_dir / "circuit_synth_ai"
sys.path.insert(0, str(plugin_dir))

from schematic_utils import SchematicParser, analyze_schematic_for_pcb


def analyze_single_schematic(schematic_path: str, verbose: bool = False):
    """Analyze a single schematic file."""
    parser = SchematicParser(schematic_path)
    
    if not parser.load_schematic():
        print(f"❌ Failed to load schematic: {schematic_path}")
        return False
    
    print(f"🔍 Analyzing schematic: {Path(schematic_path).name}")
    print("=" * 50)
    
    # Get basic stats
    stats = parser.get_schematic_stats()
    if not stats:
        print("❌ Failed to parse schematic data")
        return False
    
    # Display results
    print(f"📊 Schematic Statistics:")
    print(f"   • Total components: {stats['total_components']}")
    print(f"   • Total nets/wires: {stats['total_nets']}")
    print(f"   • Total labels: {stats['total_labels']}")
    print(f"   • Component libraries: {len(stats['component_types'])}")
    
    if stats['component_types']:
        print(f"\n📚 Component Types:")
        for lib, count in sorted(stats['component_types'].items()):
            print(f"   • {lib}: {count} components")
    
    if verbose:
        print(f"\n🔧 Component Details:")
        components = parser.get_components()
        for i, comp in enumerate(components[:10]):  # Show first 10
            print(f"   {i+1}. {comp['reference']} ({comp['lib_id']}) = {comp['value']}")
        
        if len(components) > 10:
            print(f"   ... and {len(components) - 10} more components")
            
        print(f"\n🔗 Net Information:")
        nets = parser.get_nets()
        wire_nets = [n for n in nets if n['type'] == 'wire']
        label_nets = [n for n in nets if n['type'] == 'label']
        
        print(f"   • {len(wire_nets)} wire connections")
        print(f"   • {len(label_nets)} labels")
        
        if label_nets:
            print(f"   Labels found:")
            for label in label_nets[:5]:  # Show first 5 labels
                print(f"     - {label['name']}")
    
    return True


def analyze_project_directory(project_dir: str, verbose: bool = False):
    """Analyze all schematic files in a project directory."""
    project_path = Path(project_dir)
    
    if not project_path.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return False
    
    # Find all .kicad_sch files
    schematic_files = list(project_path.glob("*.kicad_sch"))
    
    if not schematic_files:
        print(f"❌ No schematic files found in: {project_dir}")
        return False
    
    print(f"🚀 Circuit-Synth Schematic Analysis")
    print(f"📁 Project: {project_path.name}")
    print(f"📄 Found {len(schematic_files)} schematic file(s)")
    print("=" * 60)
    
    success_count = 0
    for schematic_file in schematic_files:
        print()
        if analyze_single_schematic(str(schematic_file), verbose):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Analysis complete: {success_count}/{len(schematic_files)} files processed")
    
    return success_count > 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze KiCad schematic files with Circuit-Synth AI"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "schematic_file", 
        nargs="?",
        help="Path to a single .kicad_sch file to analyze"
    )
    group.add_argument(
        "--project", "-p",
        help="Path to a project directory containing .kicad_sch files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed component and net information"
    )
    
    parser.add_argument(
        "--json", "-j",
        action="store_true", 
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    if args.schematic_file:
        # Analyze single file
        schematic_path = Path(args.schematic_file)
        if not schematic_path.exists():
            print(f"❌ Schematic file not found: {args.schematic_file}")
            sys.exit(1)
            
        if not schematic_path.suffix == '.kicad_sch':
            print(f"❌ File must be a .kicad_sch file: {args.schematic_file}")
            sys.exit(1)
        
        if args.json:
            # JSON output for single file
            parser_obj = SchematicParser(str(schematic_path))
            stats = parser_obj.get_schematic_stats()
            if stats:
                print(json.dumps(stats, indent=2))
            else:
                print('{"error": "Failed to parse schematic"}')
        else:
            success = analyze_single_schematic(str(schematic_path), args.verbose)
            sys.exit(0 if success else 1)
            
    elif args.project:
        # Analyze project directory
        if args.json:
            print('{"error": "JSON output not supported for project analysis yet"}')
            sys.exit(1)
        
        success = analyze_project_directory(args.project, args.verbose)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()