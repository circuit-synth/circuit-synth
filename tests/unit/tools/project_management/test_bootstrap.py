"""Unit tests for the cs-bootstrap one-command project creator.

Subprocess calls (uv) are mocked, so these assert the *command sequence and install
source* without running uv, building anything, or touching the network. The install
source is the load-bearing behavior: PyPI by default, editable fork only when opted
into via --editable or CIRCUIT_SYNTH_FORK.
"""

from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from circuit_synth.tools.project_management import bootstrap


@pytest.fixture
def fake_uv(monkeypatch):
    """Pretend uv exists and record every command _run would execute."""
    calls = []

    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "/usr/bin/uv")

    def _fake_run(cmd, cwd=None):
        calls.append((list(cmd), str(cwd) if cwd else None))

    monkeypatch.setattr(bootstrap, "_run", _fake_run)
    # Skip the real generate/verify (no scaffold exists on disk under the mock).
    monkeypatch.setattr(bootstrap, "_verify_schematic", lambda p: None)
    return calls


def _uv_add_cmds(calls):
    return [c for c, _ in calls if c[:2] == ["uv", "add"]]


def test_default_install_is_pypi(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    result = CliRunner().invoke(
        bootstrap.main, ["MyBoard", "--base-dir", str(tmp_path), "--no-generate"]
    )
    assert result.exit_code == 0, result.output
    adds = _uv_add_cmds(fake_uv)
    assert adds == [["uv", "add", "circuit-synth"]]
    # uv init ran in the base dir with the project name.
    assert (["uv", "init", "MyBoard"], str(tmp_path)) in fake_uv


def test_editable_flag_installs_fork(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    fork = tmp_path / "fork"
    fork.mkdir()
    (fork / "pyproject.toml").write_text("[project]\nname='x'\n")

    result = CliRunner().invoke(
        bootstrap.main,
        ["MyBoard", "--base-dir", str(tmp_path), "--editable", str(fork), "--no-generate"],
    )
    assert result.exit_code == 0, result.output
    adds = _uv_add_cmds(fake_uv)
    assert adds == [["uv", "add", "--editable", str(fork.resolve())]]


def test_env_var_selects_fork_when_no_flag(fake_uv, tmp_path, monkeypatch):
    fork = tmp_path / "envfork"
    fork.mkdir()
    (fork / "pyproject.toml").write_text("[project]\nname='x'\n")
    monkeypatch.setenv(bootstrap.FORK_ENV_VAR, str(fork))

    result = CliRunner().invoke(
        bootstrap.main, ["MyBoard", "--base-dir", str(tmp_path), "--no-generate"]
    )
    assert result.exit_code == 0, result.output
    assert _uv_add_cmds(fake_uv) == [["uv", "add", "--editable", str(fork.resolve())]]


def test_explicit_flag_overrides_env(fake_uv, tmp_path, monkeypatch):
    envfork = tmp_path / "envfork"
    envfork.mkdir()
    (envfork / "pyproject.toml").write_text("[project]\nname='x'\n")
    flagfork = tmp_path / "flagfork"
    flagfork.mkdir()
    (flagfork / "pyproject.toml").write_text("[project]\nname='y'\n")
    monkeypatch.setenv(bootstrap.FORK_ENV_VAR, str(envfork))

    result = CliRunner().invoke(
        bootstrap.main,
        ["B", "--base-dir", str(tmp_path), "--editable", str(flagfork), "--no-generate"],
    )
    assert result.exit_code == 0, result.output
    assert _uv_add_cmds(fake_uv) == [["uv", "add", "--editable", str(flagfork.resolve())]]


def test_scaffold_is_headless_and_quick(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    result = CliRunner().invoke(
        bootstrap.main,
        ["B", "--base-dir", str(tmp_path), "--circuits", "resistor,led", "--no-generate"],
    )
    assert result.exit_code == 0, result.output
    scaffold = [c for c, _ in fake_uv if c[:3] == ["uv", "run", "cs-new-project"]]
    assert scaffold, fake_uv
    cmd = scaffold[0]
    assert "--quick" in cmd and "--skip-kicad-check" in cmd
    assert "--circuits" in cmd and "resistor,led" in cmd


def test_pypi_spec_is_pinnable(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    result = CliRunner().invoke(
        bootstrap.main,
        ["B", "--base-dir", str(tmp_path), "--pypi-spec", "circuit-synth==0.12.1", "--no-generate"],
    )
    assert result.exit_code == 0, result.output
    assert _uv_add_cmds(fake_uv) == [["uv", "add", "circuit-synth==0.12.1"]]


def test_invalid_name_rejected(fake_uv, tmp_path):
    result = CliRunner().invoke(
        bootstrap.main, ["_bad", "--base-dir", str(tmp_path), "--no-generate"]
    )
    assert result.exit_code != 0
    assert "not a valid project name" in result.output


def test_existing_dir_rejected(fake_uv, tmp_path):
    (tmp_path / "Taken").mkdir()
    result = CliRunner().invoke(
        bootstrap.main, ["Taken", "--base-dir", str(tmp_path), "--no-generate"]
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_missing_uv_is_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: None)
    result = CliRunner().invoke(
        bootstrap.main, ["B", "--base-dir", str(tmp_path), "--no-generate"]
    )
    assert result.exit_code != 0
    assert "uv is required" in result.output


def test_editable_path_without_pyproject_rejected(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    notafork = tmp_path / "notafork"
    notafork.mkdir()
    result = CliRunner().invoke(
        bootstrap.main,
        ["B", "--base-dir", str(tmp_path), "--editable", str(notafork), "--no-generate"],
    )
    assert result.exit_code != 0
    assert "not a Python project" in result.output
