"""Unit tests for KiCad symbol directory environment lookup."""

import pytest

from circuit_synth.core.kicad_env import SYMBOL_DIR_ENV_VARS, kicad_symbol_dir_env


@pytest.fixture(autouse=True)
def _clear_symbol_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in SYMBOL_DIR_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_unset_returns_empty() -> None:
    assert kicad_symbol_dir_env() == ""


def test_generic_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KICAD_SYMBOL_DIR", "/a")
    assert kicad_symbol_dir_env() == "/a"


def test_versioned_variable_used_when_generic_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KICAD10_SYMBOL_DIR", "/k10")
    assert kicad_symbol_dir_env() == "/k10"


def test_generic_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KICAD10_SYMBOL_DIR", "/k10")
    monkeypatch.setenv("KICAD_SYMBOL_DIR", "/a")
    assert kicad_symbol_dir_env() == "/a"


def test_newest_version_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KICAD8_SYMBOL_DIR", "/k8")
    monkeypatch.setenv("KICAD9_SYMBOL_DIR", "/k9")
    assert kicad_symbol_dir_env() == "/k9"
