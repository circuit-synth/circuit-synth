"""cs-bootstrap: create a ready-to-use circuit-synth project in one command.

Folds the whole first-run flow -- ``uv init`` -> install circuit-synth ->
``cs-new-project --quick`` -> (optional) generate -> verify -- into a single,
cross-platform console script, retiring the machine-specific ``new-cs-project.ps1``.

Install source (decision, see module docstring in the repo notes):
- **Default = PyPI** (``uv add circuit-synth``), so nothing here hardcodes a local
  path and the tool is safe to ship publicly.
- **Editable local fork = opt-in**, via ``--editable <path>`` or the
  ``CIRCUIT_SYNTH_FORK`` environment variable. Used for local development against a
  patched checkout; never the default.

Examples::

    # Public / normal use: install circuit-synth from PyPI
    cs-bootstrap MyBoard

    # Pick starter circuits
    cs-bootstrap MyBoard --circuits resistor,led

    # Local dev against a patched fork (or set CIRCUIT_SYNTH_FORK)
    cs-bootstrap MyBoard --editable /path/to/circuit-synth
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click

# Environment override that points at a local circuit-synth checkout to install
# editable. Lets the dev machine use the fork without hardcoding a path anywhere.
FORK_ENV_VAR = "CIRCUIT_SYNTH_FORK"

# Same idea for the sibling kicad-sch-api fork. In --editable mode the project's
# .venv otherwise resolves kicad-sch-api from PyPI (0.5.5), which lacks the fork's
# save-crash fixes (instance project-name consistency, zero-length-wire guard).
KSA_FORK_ENV_VAR = "KICAD_SCH_API_FORK"

# uv rejects package names with a leading underscore; keep to a sane subset.
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    """Run a command with inherited stdio; raise a ClickException on failure.

    Output is streamed (not captured) so the user sees live progress and we sidestep
    the Windows cp1252 emoji-capture pitfall entirely. PYTHONUTF8 is set defensively.
    """
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    printable = " ".join(cmd)
    click.secho(f"$ {printable}", fg="bright_black")
    try:
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
    except FileNotFoundError:
        raise click.ClickException(
            f"'{cmd[0]}' not found on PATH. Install uv (https://docs.astral.sh/uv/) "
            f"and try again."
        )
    if result.returncode != 0:
        raise click.ClickException(
            f"step failed (exit {result.returncode}): {printable}"
        )


def _resolve_editable(editable: Optional[str]) -> Optional[str]:
    """Absolute path to a local fork to install editable, or None for the PyPI path.

    Precedence: explicit ``--editable`` wins; otherwise the ``CIRCUIT_SYNTH_FORK``
    env var (if set). An absolute path is returned so the project keeps working if
    it is later moved.
    """
    candidate = editable or os.environ.get(FORK_ENV_VAR)
    if not candidate:
        return None
    path = Path(candidate).expanduser().resolve()
    if not (path / "pyproject.toml").exists():
        raise click.ClickException(
            f"editable source '{path}' is not a Python project (no pyproject.toml)"
        )
    return str(path)


def _resolve_ksa_fork(
    cs_fork_path: Optional[str], ksa_editable: Optional[str]
) -> Optional[str]:
    """Absolute path to a local kicad-sch-api fork to install editable, or None.

    Only consulted in editable mode. Precedence: explicit ``--ksa-editable`` /
    ``KICAD_SCH_API_FORK`` wins; otherwise a **sibling checkout**
    ``<cs_fork>/../kicad-sch-api``. Returns None (PyPI kicad-sch-api) when neither
    resolves. An explicit path without a ``pyproject.toml`` is an error; a missing
    sibling is not (it just means "no fork available").
    """
    candidate = ksa_editable or os.environ.get(KSA_FORK_ENV_VAR)
    if not candidate and cs_fork_path:
        sibling = Path(cs_fork_path).resolve().parent / "kicad-sch-api"
        if (sibling / "pyproject.toml").exists():
            candidate = str(sibling)
    if not candidate:
        return None
    path = Path(candidate).expanduser().resolve()
    if not (path / "pyproject.toml").exists():
        raise click.ClickException(
            f"kicad-sch-api source '{path}' is not a Python project (no pyproject.toml)"
        )
    return str(path)


@click.command()
@click.argument("project_name")
@click.option(
    "--base-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Directory to create the project in (default: current directory).",
)
@click.option(
    "--editable",
    type=str,
    default=None,
    help=(
        "Install circuit-synth editable from this local checkout instead of PyPI "
        f"(dev use). Falls back to the {FORK_ENV_VAR} env var."
    ),
)
@click.option(
    "--ksa-editable",
    type=str,
    default=None,
    help=(
        "Install kicad-sch-api editable from this local checkout (editable mode "
        f"only). Falls back to the {KSA_FORK_ENV_VAR} env var, then a sibling "
        "../kicad-sch-api checkout."
    ),
)
@click.option(
    "--pypi-spec",
    type=str,
    default="circuit-synth",
    show_default=True,
    help="PyPI requirement to install when not using --editable (e.g. pin a version).",
)
@click.option(
    "--circuits",
    type=str,
    default=None,
    help="Comma-separated starter circuits passed to cs-new-project (e.g. resistor,led).",
)
@click.option("--no-agents", is_flag=True, help="Skip the Claude .claude/ setup.")
@click.option(
    "--generate/--no-generate",
    default=True,
    show_default=True,
    help="Run the scaffold's main.py to produce the KiCad schematic/BOM/PDF.",
)
def main(
    project_name: str,
    base_dir: Optional[str],
    editable: Optional[str],
    ksa_editable: Optional[str],
    pypi_spec: str,
    circuits: Optional[str],
    no_agents: bool,
    generate: bool,
):
    """Create and initialize a new circuit-synth project called PROJECT_NAME."""
    if not _NAME_RE.match(project_name):
        raise click.ClickException(
            f"'{project_name}' is not a valid project name "
            f"(letters/digits/_/-, no leading underscore or digit)."
        )
    if shutil.which("uv") is None:
        raise click.ClickException(
            "uv is required but not on PATH. Install it from https://docs.astral.sh/uv/."
        )

    base = Path(base_dir).expanduser().resolve() if base_dir else Path.cwd()
    project_path = base / project_name
    if project_path.exists():
        raise click.ClickException(f"'{project_path}' already exists.")

    fork_path = _resolve_editable(editable)
    source_desc = f"editable fork {fork_path}" if fork_path else f"PyPI ({pypi_spec})"
    click.secho(f"Creating circuit-synth project '{project_name}' in {base}", fg="cyan")
    click.secho(f"  circuit-synth source: {source_desc}", fg="cyan")

    # 1. uv init
    _run(["uv", "init", project_name], cwd=base)

    # 2. install circuit-synth (editable fork for dev, else PyPI)
    if fork_path:
        _run(["uv", "add", "--editable", fork_path], cwd=project_path)
        # 2b. In editable mode also wire the sibling kicad-sch-api fork through
        #     pyproject/uv.lock so it survives `uv run` re-syncs. Without this the
        #     .venv resolves PyPI kicad-sch-api 0.5.5, which lacks the fork's
        #     save-crash fixes (mixed instance project names -> KiCad save crash).
        ksa_fork = _resolve_ksa_fork(fork_path, ksa_editable)
        if ksa_fork:
            click.secho(f"  kicad-sch-api source: editable fork {ksa_fork}", fg="cyan")
            _run(["uv", "add", "--editable", ksa_fork], cwd=project_path)
        else:
            click.secho(
                "  kicad-sch-api will come from PyPI (0.5.5), which lacks the "
                "fork's save-crash fixes; set KICAD_SCH_API_FORK or check out "
                "../kicad-sch-api next to the circuit-synth fork.",
                fg="yellow",
            )
    else:
        _run(["uv", "add", pypi_spec], cwd=project_path)

    # 3. scaffold non-interactively. --skip-kicad-check keeps it headless (KiCad is
    #    only needed later to open the result); --quick avoids all prompts.
    scaffold = ["uv", "run", "cs-new-project", "--quick", "--skip-kicad-check"]
    if circuits:
        scaffold += ["--circuits", circuits]
    if no_agents:
        scaffold.append("--no-agents")
    _run(scaffold, cwd=project_path)

    # 4. optionally generate the KiCad outputs from the scaffolded main.py
    main_py = project_path / "circuit-synth" / "main.py"
    if generate and main_py.exists():
        _run(["uv", "run", "python", "circuit-synth/main.py"], cwd=project_path)
        _verify_schematic(project_path)

    _print_next_steps(project_path, generated=generate and main_py.exists())


def _verify_schematic(project_path: Path) -> None:
    """Warn (don't fail) if generation didn't produce a real schematic."""
    scharts = [p for p in project_path.rglob("*.kicad_sch") if ".venv" not in p.parts]
    if not scharts:
        click.secho(
            "  note: no .kicad_sch was produced (open the project and run main.py "
            "to see the error).",
            fg="yellow",
        )
        return
    sch = scharts[0]
    text = sch.read_text(encoding="utf-8", errors="replace")
    sym_count = text.count("(symbol ")
    click.secho(
        f"  verified {sch.name}: {sym_count} symbol block(s)",
        fg="green" if sym_count >= 1 else "yellow",
    )


def _print_next_steps(project_path: Path, generated: bool) -> None:
    click.secho("\nProject ready.", fg="green", bold=True)
    click.echo(f"  Location: {project_path}")
    if generated:
        click.echo(
            "  Generated: KiCad schematic + BOM + PDF (open the .kicad_pro in KiCad 10)."
        )
    click.echo(
        "\nTo design a circuit conversationally, open THIS folder as the workspace\n"
        "in Claude Code (that activates the project's design-circuit skill and the\n"
        "kicad-sch-api MCP from .mcp.json), then describe the circuit you want."
    )


if __name__ == "__main__":
    main()
