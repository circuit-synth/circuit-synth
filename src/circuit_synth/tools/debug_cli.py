#!/usr/bin/env python3
"""
Circuit Debugging CLI Tool

Interactive command-line interface for circuit debugging and troubleshooting.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from circuit_synth.debugging import (
    CircuitDebugger,
    DebugKnowledgeBase,
    DebugSession,
    MeasurementType,
    SymptomAnalyzer,
    TestGuidance,
    TestMeasurement,
)


class DebugCLI:
    """Command-line interface for circuit debugging"""

    def __init__(self):
        self.debugger = CircuitDebugger()
        self.analyzer = SymptomAnalyzer()
        self.knowledge_base = DebugKnowledgeBase()
        self.current_session: Optional[DebugSession] = None

    def start_session(
        self, board_name: str, board_version: str = "1.0", symptoms: List[str] = None
    ):
        """Start a new debugging session"""
        self.current_session = self.debugger.start_session(board_name, board_version)
        print(f"✅ Started debugging session for {board_name} v{board_version}")
        print(f"   Session ID: {self.current_session.session_id}")

        if symptoms:
            for symptom in symptoms:
                self.current_session.add_symptom(symptom)
            print(f"   Added {len(symptoms)} initial symptoms")

        return self.current_session

    def add_symptom(self, symptom: str):
        """Add a symptom to current session"""
        if not self.current_session:
            print("❌ No active debugging session. Use 'start' first.")
            return

        self.current_session.add_symptom(symptom)
        print(f"✅ Added symptom: {symptom}")

    def add_measurement(self, name: str, value: str, unit: str = "", notes: str = ""):
        """Add a measurement to current session"""
        if not self.current_session:
            print("❌ No active debugging session. Use 'start' first.")
            return

        # Try to parse value as float
        try:
            parsed_value = float(value)
        except ValueError:
            parsed_value = value

        self.current_session.add_measurement(name, parsed_value, unit, notes)
        print(f"✅ Added measurement: {name} = {value}{unit}")

    def analyze(self):
        """Analyze current symptoms and measurements"""
        if not self.current_session:
            print("❌ No active debugging session. Use 'start' first.")
            return

        print("\n🔍 Analyzing symptoms and measurements...\n")

        # Categorize symptoms
        categories = self.analyzer.categorize_symptoms(self.current_session.symptoms)
        if categories:
            print("📊 Symptom Categories:")
            for category, symptoms in categories.items():
                print(f"   {category.upper()}: {', '.join(symptoms)}")
            print()

        # Analyze issues
        issues = self.debugger.analyze_symptoms(self.current_session)

        if issues:
            print(f"🔧 Identified {len(issues)} potential issues:\n")
            for i, issue in enumerate(issues, 1):
                self._print_issue(i, issue)
        else:
            print(
                "ℹ️  No specific issues identified yet. Add more symptoms or measurements."
            )

        # Search knowledge base
        if self.current_session.symptoms:
            patterns = self.knowledge_base.search_patterns(
                self.current_session.symptoms
            )
            if patterns:
                print("\n📚 Similar Historical Patterns:")
                for pattern, similarity in patterns[:3]:
                    print(
                        f"\n   🔹 {pattern.root_cause} (similarity: {similarity:.0%})"
                    )
                    print(f"      Solutions: {', '.join(pattern.solutions[:2])}")

    def _print_issue(self, num: int, issue):
        """Print a formatted issue"""
        severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

        icon = severity_icons.get(issue.severity.value, "⚪")
        print(f"{num}. {icon} [{issue.severity.value.upper()}] {issue.title}")
        print(f"   Category: {issue.category.value}")
        print(f"   Confidence: {issue.confidence:.0%}")
        print(f"   Description: {issue.description}")

        if issue.probable_causes:
            print(f"   Probable Causes:")
            for cause in issue.probable_causes[:3]:
                print(f"      • {cause}")

        if issue.test_suggestions:
            print(f"   Next Tests:")
            for test in issue.test_suggestions[:3]:
                print(f"      → {test}")

        if issue.solutions:
            print(f"   Potential Solutions:")
            for solution in issue.solutions[:2]:
                print(f"      ✓ {solution}")
        print()

    def suggest_tests(self):
        """Suggest next debugging steps"""
        if not self.current_session:
            print("❌ No active debugging session. Use 'start' first.")
            return

        suggestions = self.debugger.suggest_next_test(self.current_session)

        print("\n🎯 Suggested Next Steps:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")

    def show_troubleshooting_tree(self, issue_type: str):
        """Display a troubleshooting tree"""
        trees = {
            "power": TestGuidance.create_power_troubleshooting_tree,
            "i2c": TestGuidance.create_i2c_troubleshooting_tree,
            "usb": TestGuidance.create_usb_troubleshooting_tree,
        }

        if issue_type not in trees:
            print(f"❌ Unknown issue type. Available: {', '.join(trees.keys())}")
            return

        tree = trees[issue_type]()
        print(tree.to_markdown())

    def search_history(self, keywords: List[str]):
        """Search debugging history"""
        patterns = self.knowledge_base.search_patterns(keywords)

        if patterns:
            print(f"\n📚 Found {len(patterns)} historical patterns:\n")
            for pattern, similarity in patterns:
                print(f"Pattern: {pattern.root_cause}")
                print(f"Similarity: {similarity:.0%}")
                print(f"Category: {pattern.category}")
                print(f"Symptoms: {', '.join(pattern.symptoms[:3])}")
                print(f"Solutions: {', '.join(pattern.solutions[:2])}")
                print(f"Success Rate: {pattern.success_rate:.0%}")
                print(f"Occurrences: {pattern.occurrence_count}")
                print("-" * 50)
        else:
            print("No matching patterns found.")

    def close_session(self, resolution: str, root_cause: str):
        """Close current debugging session"""
        if not self.current_session:
            print("❌ No active debugging session.")
            return

        self.debugger.close_session(self.current_session, resolution, root_cause)
        print(f"✅ Session closed successfully")
        print(f"   Root Cause: {root_cause}")
        print(f"   Resolution: {resolution}")

        # Calculate duration
        duration = (
            self.current_session.ended_at - self.current_session.started_at
        ).total_seconds() / 60
        print(f"   Duration: {duration:.1f} minutes")

        self.current_session = None

    def export_session(self, filename: str):
        """Export current session to file"""
        if not self.current_session:
            print("❌ No active debugging session.")
            return

        output_path = Path(filename)
        with open(output_path, "w") as f:
            json.dump(self.current_session.to_dict(), f, indent=2)

        print(f"✅ Session exported to {output_path}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Circuit Debugging Assistant - AI-powered PCB troubleshooting"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start debugging session")
    start_parser.add_argument("board", help="Board name")
    start_parser.add_argument("--version", default="1.0", help="Board version")
    start_parser.add_argument("--symptoms", nargs="+", help="Initial symptoms")

    # Symptom command
    symptom_parser = subparsers.add_parser("symptom", help="Add symptom")
    symptom_parser.add_argument("description", help="Symptom description")

    # Measure command
    measure_parser = subparsers.add_parser("measure", help="Add measurement")
    measure_parser.add_argument("name", help="Measurement name")
    measure_parser.add_argument("value", help="Measured value")
    measure_parser.add_argument("--unit", default="", help="Unit")
    measure_parser.add_argument("--notes", default="", help="Additional notes")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze current symptoms")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest next tests")

    # Tree command
    tree_parser = subparsers.add_parser("tree", help="Show troubleshooting tree")
    tree_parser.add_argument(
        "type", choices=["power", "i2c", "usb"], help="Type of troubleshooting tree"
    )

    # History command
    history_parser = subparsers.add_parser("history", help="Search debugging history")
    history_parser.add_argument("keywords", nargs="+", help="Search keywords")

    # Close command
    close_parser = subparsers.add_parser("close", help="Close debugging session")
    close_parser.add_argument("resolution", help="How the issue was resolved")
    close_parser.add_argument("--root-cause", required=True, help="Root cause of issue")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export session to file")
    export_parser.add_argument("filename", help="Output filename")

    # Interactive mode
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )

    args = parser.parse_args()

    cli = DebugCLI()

    if args.interactive or not args.command:
        # Interactive mode
        print("🔧 Circuit Debugging Assistant - Interactive Mode")
        print("Type 'help' for available commands or 'quit' to exit\n")

        while True:
            try:
                command = input("debug> ").strip()

                if command == "quit":
                    break
                elif command == "help":
                    print(
                        """
Available commands:
  start <board> [version]  - Start debugging session
  symptom <description>     - Add symptom
  measure <name> <value>    - Add measurement
  analyze                   - Analyze symptoms
  suggest                   - Suggest next tests
  tree <type>              - Show troubleshooting tree
  history <keywords>       - Search history
  close <resolution>       - Close session
  export <filename>        - Export session
  quit                     - Exit
                    """
                    )
                elif command.startswith("start "):
                    parts = command.split()
                    board = parts[1]
                    version = parts[2] if len(parts) > 2 else "1.0"
                    cli.start_session(board, version)
                elif command.startswith("symptom "):
                    symptom = command[8:]
                    cli.add_symptom(symptom)
                elif command.startswith("measure "):
                    parts = command.split()
                    if len(parts) >= 3:
                        name = parts[1]
                        value = parts[2]
                        unit = parts[3] if len(parts) > 3 else ""
                        cli.add_measurement(name, value, unit)
                elif command == "analyze":
                    cli.analyze()
                elif command == "suggest":
                    cli.suggest_tests()
                elif command.startswith("tree "):
                    issue_type = command.split()[1]
                    cli.show_troubleshooting_tree(issue_type)
                elif command.startswith("history "):
                    keywords = command.split()[1:]
                    cli.search_history(keywords)
                elif command.startswith("export "):
                    filename = command.split()[1]
                    cli.export_session(filename)
                else:
                    print(f"Unknown command: {command}")

            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"Error: {e}")

    else:
        # Single command mode
        if args.command == "start":
            cli.start_session(args.board, args.version, args.symptoms)
        elif args.command == "symptom":
            cli.add_symptom(args.description)
        elif args.command == "measure":
            cli.add_measurement(args.name, args.value, args.unit, args.notes)
        elif args.command == "analyze":
            cli.analyze()
        elif args.command == "suggest":
            cli.suggest_tests()
        elif args.command == "tree":
            cli.show_troubleshooting_tree(args.type)
        elif args.command == "history":
            cli.search_history(args.keywords)
        elif args.command == "close":
            cli.close_session(args.resolution, args.root_cause)
        elif args.command == "export":
            cli.export_session(args.filename)


if __name__ == "__main__":
    main()
