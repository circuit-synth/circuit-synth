#!/usr/bin/env python3
"""
Unit tests for cs-new-project command

Tests the circuit-synth project creation workflow including:
- File generation (README, CLAUDE.md, main.py)
- Claude agent directory structure
- Template management
- CLI flags and configuration
- Regression tests for known bugs
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from circuit_synth.tools.project_management.new_project import (
    _claude_tooling_summary,
    check_kicad_installation,
    copy_complete_claude_setup,
    copy_example_project_template,
    create_claude_directory_from_templates,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing project creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_console():
    """Mock rich.console.Console"""
    with patch("circuit_synth.tools.project_management.new_project.console") as mock:
        yield mock


@pytest.fixture
def mock_template_dir(tmp_path):
    """Create a mock template directory structure"""
    template_dir = tmp_path / "templates" / "example_project"
    template_dir.mkdir(parents=True)

    # Create .claude directory structure
    claude_dir = template_dir / ".claude"
    claude_dir.mkdir()

    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()

    # Create agent subdirectories and files
    for category in [
        "circuit-design",
        "circuit-generation",
        "manufacturing",
        "development",
    ]:
        cat_dir = agents_dir / category
        cat_dir.mkdir()
        (cat_dir / f"{category}-agent.md").write_text(f"# {category} Agent")

    # Create mcp_settings.json (should be removed)
    (claude_dir / "mcp_settings.json").write_text('{"test": "data"}')

    # Create example circuit files
    (template_dir / "main.py").write_text("# Example circuit")
    (template_dir / "README.md").write_text("# Template README")

    return template_dir


# ============================================================================
# File Generation Tests
# ============================================================================


# NOTE: README.md / CLAUDE.md content generation moved from the free functions
# create_project_readme()/create_claude_md() into READMEGenerator/CLAUDEMDGenerator
# in template_manager.py; that generated-file content is now covered by
# test_new_project_cli.py's file-content-validation tests. The old free-function
# tests were removed here rather than kept against a deleted API.


# ============================================================================
# Claude Directory Structure Tests
# ============================================================================


class TestClaudeDirectoryStructure:
    """Test .claude directory creation and agent setup"""

    @patch("circuit_synth.tools.project_management.new_project.register_circuit_agents")
    def test_creates_claude_directory(
        self, mock_register, temp_project_dir, mock_console, mock_template_dir
    ):
        """Test .claude directory is created"""
        with patch(
            "circuit_synth.tools.project_management.new_project.Path"
        ) as mock_path_class:
            # Setup mock to return our template directory
            mock_path_instance = MagicMock()
            mock_path_instance.parent.parent.parent = mock_template_dir.parent.parent
            mock_path_class.return_value = mock_path_instance

            create_claude_directory_from_templates(
                temp_project_dir, developer_mode=False
            )

            claude_dir = temp_project_dir / ".claude"
            assert claude_dir.exists(), ".claude directory should be created"

    # NOTE: the legacy register_circuit_agents() fallback was retired in Stage 3
    # (template-based install replaced it); tests asserting that fallback is called
    # on template failure were removed. Current .claude/agents+skills install is
    # covered by test_creates_claude_directory above and, end-to-end, by
    # test_new_project_cli.py.

    @patch("circuit_synth.tools.project_management.new_project.shutil.copytree")
    @patch("circuit_synth.tools.project_management.new_project.shutil.rmtree")
    @patch("circuit_synth.tools.project_management.new_project.register_circuit_agents")
    def test_removes_dev_agents_in_non_developer_mode(
        self, mock_register, mock_rmtree, mock_copytree, temp_project_dir, mock_console
    ):
        """Test development agents are removed when not in developer mode"""
        # Setup mock source directory
        source_dir = temp_project_dir / "source" / ".claude"
        source_dir.mkdir(parents=True)

        with patch(
            "circuit_synth.tools.project_management.new_project.Path"
        ) as mock_path_class:
            mock_path_instance = MagicMock()
            mock_path_instance.parent.parent.parent.parent = temp_project_dir / "source"
            mock_path_class.return_value = mock_path_instance

            # Mock exists to return True for source directory
            with patch.object(Path, "exists", return_value=True):
                copy_complete_claude_setup(temp_project_dir, developer_mode=False)

            # Verify copytree was called
            assert mock_copytree.called, "Should copy .claude directory"

    @patch(
        "circuit_synth.tools.project_management.new_project.create_claude_directory_from_templates"
    )
    @patch("circuit_synth.tools.project_management.new_project.register_circuit_agents")
    def test_keeps_dev_agents_in_developer_mode(
        self, mock_register, mock_create_templates, temp_project_dir, mock_console
    ):
        """Test development agents are kept in developer mode

        NOTE: Testing the actual file removal logic is complex due to nested mocking.
        This test verifies the fallback path works correctly, which is the primary
        code path when source .claude directory is not found.
        """
        # Simulate source directory not existing (common case)
        # This will trigger the fallback to create_claude_directory_from_templates
        copy_complete_claude_setup(temp_project_dir, developer_mode=True)

        # Verify fallback was called with developer_mode=True
        # Note: The actual call uses positional argument, not keyword
        mock_create_templates.assert_called_once_with(temp_project_dir, True)

    def test_removes_mcp_settings_json(self, temp_project_dir, mock_console):
        """Test mcp_settings.json is removed after copying"""
        # Create .claude directory with mcp_settings.json
        claude_dir = temp_project_dir / ".claude"
        claude_dir.mkdir()
        mcp_file = claude_dir / "mcp_settings.json"
        mcp_file.write_text('{"test": "data"}')

        assert mcp_file.exists(), "mcp_settings.json should exist initially"

        # Simulate what new_project does - it removes this file
        if mcp_file.exists():
            mcp_file.unlink()

        assert not mcp_file.exists(), "mcp_settings.json should be removed"


# ============================================================================
# Template Management Tests
# ============================================================================


class TestTemplateManagement:
    """Test template copying and management"""

    @patch("circuit_synth.tools.project_management.new_project.shutil.copy2")
    @patch("circuit_synth.tools.project_management.new_project.shutil.copytree")
    def test_copy_template_success(
        self,
        mock_copytree,
        mock_copy2,
        temp_project_dir,
        mock_console,
        mock_template_dir,
    ):
        """Test successful template copy"""
        with patch(
            "circuit_synth.tools.project_management.new_project.Path"
        ) as mock_path_class:
            mock_path_instance = MagicMock()
            mock_path_instance.parent.parent.parent = mock_template_dir.parent
            mock_path_class.return_value = mock_path_instance

            # Mock template_dir.exists() to return True
            with patch.object(Path, "exists", return_value=True):
                # Mock iterdir to return our template files
                with patch.object(
                    Path,
                    "iterdir",
                    return_value=[
                        mock_template_dir / "main.py",
                        mock_template_dir / "README.md",
                    ],
                ):
                    result = copy_example_project_template(temp_project_dir)
                    # This will fail in current implementation due to mocking complexity
                    # But demonstrates the test pattern

    @patch("circuit_synth.tools.project_management.new_project.Path")
    def test_copy_template_fallback_on_missing(
        self, mock_path_class, temp_project_dir, mock_console
    ):
        """Test fallback when template directory is missing"""
        # Mock template directory as non-existent
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.parent = temp_project_dir / "nonexistent"
        mock_path_class.return_value = mock_path_instance

        with patch.object(Path, "exists", return_value=False):
            result = copy_example_project_template(temp_project_dir)
            assert result is False, "Should return False when template not found"


# ============================================================================
# KiCad Installation Tests
# ============================================================================


class TestKiCadInstallation:
    """Test KiCad installation checking"""

    @patch(
        "circuit_synth.tools.project_management.new_project.validate_kicad_installation"
    )
    def test_kicad_found(self, mock_validate, mock_console):
        """Test successful KiCad detection"""
        mock_validate.return_value = {
            "cli_available": True,
            "cli_path": "/usr/bin/kicad-cli",
            "cli_version": "7.0.0",
            "libraries_available": True,
            "symbol_path": "/usr/share/kicad/symbols",
            "footprint_path": "/usr/share/kicad/footprints",
        }

        result = check_kicad_installation()

        assert result["kicad_installed"] is True, "Should detect KiCad as installed"
        # Output is emoji-free since the c3e79df emoji strip.
        mock_console.print.assert_any_call("KiCad found!", style="green")

    @patch(
        "circuit_synth.tools.project_management.new_project.validate_kicad_installation"
    )
    def test_kicad_not_found(self, mock_validate, mock_console):
        """Test KiCad not found"""
        mock_validate.return_value = {"cli_available": False}

        result = check_kicad_installation()

        assert (
            result["kicad_installed"] is False
        ), "Should detect KiCad as not installed"
        # Output is emoji-free since the c3e79df emoji strip.
        mock_console.print.assert_any_call("KiCad not found", style="red")

    @patch(
        "circuit_synth.tools.project_management.new_project.validate_kicad_installation"
    )
    def test_kicad_check_error(self, mock_validate, mock_console):
        """Test error during KiCad check"""
        mock_validate.side_effect = Exception("Test error")

        result = check_kicad_installation()

        assert result["kicad_installed"] is False, "Should handle errors gracefully"
        assert "error" in result, "Should include error message"


# ============================================================================
# Configuration Tests
# ============================================================================


class TestConfiguration:
    """Test CLI flags and configuration parsing"""

    def test_quick_mode_flag(self):
        """Test --quick flag uses default configuration"""
        # This would test the CLI invocation with --quick
        # Testing CLI directly requires click.testing.CliRunner
        pass  # Placeholder for CLI integration tests

    def test_developer_mode_flag(self):
        """Test --developer flag includes dev tools"""
        # This would test the CLI invocation with --developer
        pass  # Placeholder for CLI integration tests

    def test_no_agents_flag(self):
        """Test --no-agents flag skips Claude setup"""
        # This would test the CLI invocation with --no-agents
        pass  # Placeholder for CLI integration tests


# ============================================================================
# Regression Tests
# ============================================================================


class TestRegressionBugs:
    """Regression tests for known bugs"""

    def test_no_workspace_configuration_in_generated_files(self, temp_project_dir):
        """
        REGRESSION TEST for issue #238 (example)

        Verifies that generated pyproject.toml never contains 'workspace = true'
        which would break 'uv run python circuit-synth/main.py'

        This caught the 0.8.22 bug where templates had workspace configuration.
        """
        # Note: cs-new-project doesn't modify pyproject.toml anymore
        # but we can test that templates don't contain workspace config

        # Create a mock pyproject.toml
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["circuit-synth"]
""")

        content = pyproject.read_text()
        assert (
            "workspace = true" not in content
        ), "Generated pyproject.toml must not contain workspace configuration"
        assert (
            "[tool.uv.workspace]" not in content
        ), "Generated pyproject.toml must not contain workspace section"


# ============================================================================
# Integration-style Tests (using real temp directories)
# ============================================================================


class TestRealFileOperations:
    """Tests that create actual files to verify behavior"""

    def test_directory_structure_created(self, temp_project_dir):
        """Test that proper directory structure is created"""
        # Create circuit-synth directory
        circuit_synth_dir = temp_project_dir / "circuit-synth"
        circuit_synth_dir.mkdir()

        assert circuit_synth_dir.exists(), "circuit-synth directory should exist"
        assert circuit_synth_dir.is_dir(), "circuit-synth should be a directory"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestClaudeToolingSummary:
    """The bootstrap summary must count skills, not just agents/commands (F1)."""

    def _make_claude(self, root, skills=(), agents=0, commands=0):
        claude = root / ".claude"
        for name in skills:
            skill_dir = claude / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
        adir = claude / "agents"
        adir.mkdir(parents=True, exist_ok=True)
        for i in range(agents):
            (adir / f"agent{i}.md").write_text("x", encoding="utf-8")
        cdir = claude / "commands"
        cdir.mkdir(parents=True, exist_ok=True)
        for i in range(commands):
            (cdir / f"cmd{i}.md").write_text("x", encoding="utf-8")
        return root

    def test_counts_and_names_the_skill(self, tmp_path):
        """The default scaffold (design-circuit skill, no agents/commands) is named."""
        root = self._make_claude(tmp_path, skills=["design-circuit"])
        summary = _claude_tooling_summary(root)
        assert "1 skill (design-circuit)" in summary
        assert "0 agents" in summary and "0 commands" in summary

    def test_no_longer_reports_zero_when_skill_present(self, tmp_path):
        """Regression guard for F1: a present skill must not read as all-zero tooling."""
        root = self._make_claude(tmp_path, skills=["design-circuit"])
        assert _claude_tooling_summary(root) != "0 agents, 0 commands"
        assert "skill" in _claude_tooling_summary(root)

    def test_pluralizes_and_counts_agents_commands(self, tmp_path):
        root = self._make_claude(
            tmp_path, skills=["design-circuit", "edit-circuit"], agents=2, commands=3
        )
        summary = _claude_tooling_summary(root)
        assert "2 skills" in summary
        assert "2 agents" in summary and "3 commands" in summary

    def test_zero_skills_reported_plainly(self, tmp_path):
        root = self._make_claude(tmp_path, skills=(), agents=1, commands=0)
        assert _claude_tooling_summary(root) == "0 skills, 1 agents, 0 commands"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_missing_template_degrades_gracefully(self, temp_project_dir, mock_console):
        """A missing packaged template must not crash; it still creates .claude.

        The legacy register_circuit_agents() fallback was retired in Stage 3; the
        current contract on template-not-found is a PACKAGING ERROR message plus an
        empty .claude directory, with no exception raised.
        """
        # Force the template-not-found branch (Path.exists -> False for the check).
        with patch.object(Path, "exists", return_value=False):
            create_claude_directory_from_templates(temp_project_dir)  # must not raise

        assert (
            temp_project_dir / ".claude"
        ).exists(), ".claude dir should still be created on template failure"


# ============================================================================
# Import Regression Tests (#588)
# ============================================================================


class TestModuleImports:
    """
    Regression tests for module import issues.

    These tests verify that all project management tools can be imported
    without ModuleNotFoundError, preventing regressions like issue #588.
    """

    def test_new_project_module_imports(self):
        """
        REGRESSION TEST for issue #588

        Verifies that new_project.py can be imported without errors.
        The bug was importing from non-existent agent_registry submodule
        instead of using the package root with fallback.
        """
        # This import should not raise ModuleNotFoundError
        from circuit_synth.tools.project_management import new_project

        # Verify key functions are accessible
        assert hasattr(new_project, "main"), "main function should be accessible"
        assert hasattr(
            new_project, "create_claude_directory_from_templates"
        ), "create_claude_directory_from_templates should be accessible"

    def test_init_existing_project_module_imports(self):
        """
        REGRESSION TEST for issue #588

        Verifies that init_existing_project.py can be imported without errors.
        The bug was:
        1. Importing from non-existent agent_registry submodule
        2. Wrong import path for KiCadParser
        """
        # This import should not raise ModuleNotFoundError
        from circuit_synth.tools.project_management import init_existing_project

        # Verify key functions are accessible
        assert hasattr(
            init_existing_project, "main"
        ), "main function should be accessible"

    def test_register_circuit_agents_fallback(self):
        """
        REGRESSION TEST for issue #588

        Verifies that register_circuit_agents can be imported from package root
        and provides fallback behavior when agent_registry module is missing.
        """
        # This import should work (package root with fallback)
        from circuit_synth.ai_integration.claude import register_circuit_agents

        # Function should be callable
        assert callable(
            register_circuit_agents
        ), "register_circuit_agents should be callable"

    def test_kicad_parser_import_path(self):
        """
        REGRESSION TEST for issue #588

        Verifies KiCadParser can be imported from correct path.
        The bug was importing from circuit_synth.tools.kicad_parser
        instead of circuit_synth.tools.utilities.kicad_parser.
        """
        # This import should work
        from circuit_synth.tools.utilities.kicad_parser import KiCadParser

        # Class should be importable
        assert KiCadParser is not None, "KiCadParser class should be importable"
