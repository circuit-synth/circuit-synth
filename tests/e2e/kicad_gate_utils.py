"""Shared KiCad save-crash gate helper for e2e tests.

The gate reproduces a KiCad GUI save headlessly: copy a ``.kicad_sch``, run
``kicad-cli sch upgrade --force`` on the copy (KiCad's own writer), and assert
the write round-trips. It exists because bug #B (multi-unit dangling instance
paths) segfaulted the writer on save and truncated the file to 0 bytes, while
``kicad-cli`` ERC/netlist/pdf all *loaded* the bad file happily -- only a GUI
save (or this upgrade proxy) caught it.

Bug #C: the naive form of this gate produced a false "clean" during E2E run 4.
Three traps, all hit in practice:

  1. **Pipe rc trap** -- ``kicad-cli ... | tail; echo $?`` reports *tail's* exit
     code, so a 139 segfault reads as 0. Read the returncode directly.
  2. **0-byte truncation with rc=0** -- a crash mid-write can leave a 0-byte
     file, so "rc != 139" is not a sufficient gate; assert ``size > 0``.
  3. **MSYS path trap** (Git-Bash only) -- handing the Windows ``kicad-cli.exe``
     an MSYS ``/tmp/...`` path makes it silently write a 0-byte file with rc=0.
     Always pass native Windows paths. (From Python, ``tmp_path`` is native, so
     this only bites shell scripts -- but the assertion still catches it.)

So the gate is: **rc == 0 AND filesize > 0 AND the upgraded file reloads.**
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from circuit_synth.kicad.sch_gen.erc_gate import _find_kicad_cli


def assert_kicad_save_ok(sch_path, kicad_cli: Optional[str] = None) -> None:
    """Assert KiCad can re-save ``sch_path`` without crashing.

    Copies the file, runs ``kicad-cli sch upgrade --force`` on the copy, and
    asserts ``rc == 0`` AND the copy is non-empty AND ``kicad-cli sch erc``
    reloads it. Uses ``subprocess.run`` with a list argv (no shell) so the rc is
    read directly, never through a pipe. Skips (does not fail) if kicad-cli is
    unavailable.

    See the module docstring for the three traps this guards.
    """
    sch_path = Path(sch_path)
    try:
        cli = kicad_cli or _find_kicad_cli()
    except Exception:
        pytest.skip("kicad-cli (KiCad 10) not available")

    copy = sch_path.with_name(sch_path.stem + "_savecopy.kicad_sch")
    shutil.copyfile(sch_path, copy)

    up = subprocess.run(
        [cli, "sch", "upgrade", "--force", str(copy)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert up.returncode == 0, (
        f"kicad-cli sch upgrade returned {up.returncode} on {copy.name} "
        f"(139 = segfault -> KiCad save crash). stderr: {up.stderr.strip()}"
    )
    size = copy.stat().st_size
    assert size > 0, (
        f"{copy.name} is 0 bytes after upgrade (a crash truncated it, or an MSYS "
        f"path trap); rc was {up.returncode}"
    )
    # -o keeps the .rpt beside the copy (in tmp) instead of polluting cwd.
    erc = subprocess.run(
        [cli, "sch", "erc", "-o", str(copy.with_suffix(".rpt")), str(copy)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    # ERC returns 0 (clean) or 5 (violations exist) on a *loadable* file; a
    # crash/parse failure is a different, nonzero code. Either 0/5 proves reload.
    assert erc.returncode in (0, 5), (
        f"upgraded {copy.name} failed to reload in kicad-cli sch erc "
        f"(rc={erc.returncode}). stderr: {erc.stderr.strip()}"
    )
