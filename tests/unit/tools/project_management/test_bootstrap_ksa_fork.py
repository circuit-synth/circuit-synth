"""Unit tests for cs-bootstrap wiring the sibling kicad-sch-api fork (Stage 23.4).

In --editable mode the project's .venv otherwise resolves kicad-sch-api from PyPI
(0.5.5), missing the fork's save-crash fixes. These assert the resolution
precedence and that the editable ksa fork rides `uv add --editable` (so it lands
in pyproject/uv.lock and survives `uv run` re-syncs). PyPI-default mode stays
untouched. uv is mocked -- no install, no network.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from circuit_synth.tools.project_management import bootstrap


@pytest.fixture
def fake_uv(monkeypatch):
    calls = []
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "/usr/bin/uv")
    monkeypatch.setattr(
        bootstrap, "_run", lambda cmd, cwd=None: calls.append(list(cmd))
    )
    monkeypatch.setattr(bootstrap, "_verify_schematic", lambda p: None)
    return calls


def _mkfork(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "pyproject.toml").write_text("[project]\nname='x'\n")
    return path


def _ksa_add_cmds(calls):
    return [
        c
        for c in calls
        if c[:2] == ["uv", "add"] and any("kicad-sch-api" in str(x) for x in c)
    ]


# --- _resolve_ksa_fork precedence ------------------------------------------- #


def test_resolve_prefers_explicit_option_over_sibling(tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    cs = _mkfork(tmp_path / "circuit-synth")
    _mkfork(tmp_path / "kicad-sch-api")  # sibling exists
    explicit = _mkfork(tmp_path / "elsewhere" / "kicad-sch-api")
    got = bootstrap._resolve_ksa_fork(str(cs), str(explicit))
    assert got == str(explicit.resolve())


def test_resolve_env_var_when_no_option(tmp_path, monkeypatch):
    cs = _mkfork(tmp_path / "circuit-synth")
    envfork = _mkfork(tmp_path / "envksa")
    monkeypatch.setenv(bootstrap.KSA_FORK_ENV_VAR, str(envfork))
    got = bootstrap._resolve_ksa_fork(str(cs), None)
    assert got == str(envfork.resolve())


def test_resolve_falls_back_to_sibling(tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    cs = _mkfork(tmp_path / "circuit-synth")
    sibling = _mkfork(tmp_path / "kicad-sch-api")
    got = bootstrap._resolve_ksa_fork(str(cs), None)
    assert got == str(sibling.resolve())


def test_resolve_none_when_nothing_available(tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    cs = _mkfork(tmp_path / "circuit-synth")
    assert bootstrap._resolve_ksa_fork(str(cs), None) is None


def test_resolve_rejects_path_without_pyproject(tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    cs = _mkfork(tmp_path / "circuit-synth")
    bad = tmp_path / "notafork"
    bad.mkdir()
    with pytest.raises(bootstrap.click.ClickException):
        bootstrap._resolve_ksa_fork(str(cs), str(bad))


# --- main() install-command construction ------------------------------------ #


def test_editable_with_sibling_adds_ksa_fork(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    cs = _mkfork(tmp_path / "circuit-synth")
    ksa = _mkfork(tmp_path / "kicad-sch-api")  # sibling of the cs fork
    result = CliRunner().invoke(
        bootstrap.main,
        [
            "B",
            "--base-dir",
            str(tmp_path / "out"),
            "--editable",
            str(cs),
            "--no-generate",
        ],
    )
    assert result.exit_code == 0, result.output
    ksa_adds = _ksa_add_cmds(fake_uv)
    assert ksa_adds == [["uv", "add", "--editable", str(ksa.resolve())]]
    # ...and it comes AFTER the circuit-synth editable add.
    cs_add = fake_uv.index(["uv", "add", "--editable", str(cs.resolve())])
    ksa_add = fake_uv.index(["uv", "add", "--editable", str(ksa.resolve())])
    assert cs_add < ksa_add


def test_editable_without_sibling_warns_no_ksa_cmd(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    # cs fork with NO sibling kicad-sch-api next to it.
    cs = _mkfork(tmp_path / "lonely" / "circuit-synth")
    result = CliRunner().invoke(
        bootstrap.main,
        [
            "B",
            "--base-dir",
            str(tmp_path / "out"),
            "--editable",
            str(cs),
            "--no-generate",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _ksa_add_cmds(fake_uv) == []
    assert "kicad-sch-api will come from PyPI" in result.output


def test_pypi_mode_never_touches_ksa(fake_uv, tmp_path, monkeypatch):
    monkeypatch.delenv(bootstrap.FORK_ENV_VAR, raising=False)
    monkeypatch.delenv(bootstrap.KSA_FORK_ENV_VAR, raising=False)
    result = CliRunner().invoke(
        bootstrap.main, ["B", "--base-dir", str(tmp_path / "out"), "--no-generate"]
    )
    assert result.exit_code == 0, result.output
    assert _ksa_add_cmds(fake_uv) == []
    assert "kicad-sch-api will come from PyPI" not in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
