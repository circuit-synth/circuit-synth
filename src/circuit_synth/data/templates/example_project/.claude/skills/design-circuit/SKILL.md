---
name: design-circuit
description: Design a circuit from a natural-language spec using an iterative loop — plan, write circuit-synth Python, generate the KiCad schematic, simulate with ngspice, examine results, and refine until the spec's measurable criteria pass. Use whenever the user asks to design, create, or modify a circuit or schematic in this project.
---

# design-circuit — iterative circuit design loop

You are designing a circuit in a circuit-synth project. Work in numbered
iterations (max **5**). Keep an append-only `design_log.md` in the project root;
after every iteration append: iteration number, what changed, generation result,
simulation measurements, PASS/FAIL per criterion, and the next action.

## Two modes: NEW design vs EDIT existing

- **NEW design** (no matching `.py` yet, or the user asks for a fresh circuit):
  run the full loop below starting at Phase 0.
- **EDIT an existing design** (the user asks to change/tweak/fix a circuit that
  already has a `circuit-synth/*.py` in this project — "make R3 4.7k", "add a
  bypass cap on VOUT", "raise the cutoff to 10 kHz"): jump to the
  **"Editing an existing design"** section near the end. The short version:
  change the **Python source**, regenerate in update mode (placement is
  preserved), and re-simulate — do **not** hand-edit the generated `.kicad_sch`
  for value/topology changes; the next regeneration overwrites such edits.

## Phase 0 — SETUP (once)
- Read `circuit-synth/main.py` — it is a known-good example of the API pattern.
- Windows note: run every command with UTF-8 mode, e.g. in bash
  `PYTHONUTF8=1 uv run ...` (emoji prints crash captured output otherwise).

## Phase 1 — THINK
- Restate the user's request as a spec: topology, inputs, outputs, constraints.
- Derive **measurable acceptance criteria** — concrete node voltages/currents
  with tolerances (default ±5 % unless the user specified). Example:
  "VOUT_3V3 = 3.30 V ± 5 % with VIN_5V = 5.0 V". If the request has nothing
  measurable, define at minimum: schematic generates, ERC-relevant connectivity
  is sane, expected component count.
- List every component with its intended KiCad `symbol=` and `footprint=` id.
  For a multi-sheet design (see Phase 3), group the component list by sheet
  (`### Sheet: psu`, `### Sheet: amp`, ...) so the hierarchy is visible in the log.
- Write all of this into `design_log.md` under `## Iteration N — plan`.

## Phase 2 — DISCOVER (symbol/footprint resolution)
- NEVER guess lib ids. Verify each one:
  `PYTHONUTF8=1 uv run python tools/find_symbol.py "<query>"` (add
  `--footprints` for footprints). Common: `Device:R`, `Device:C`, `Device:LED`,
  `Regulator_Linear:AMS1117-3.3`.
- **Derived symbols (`(extends ...)`) can carry the parent's pin count/pinout.**
  A KiCad symbol defined as `(extends "OtherPart")` inherits the parent's pins —
  e.g. `Amplifier_Operational:ADA4807-2ARM` extends the 8-pin `LM2904`, but the
  ADA4807-2ARMZ part is MSOP-**10**. Before wiring a derived symbol, verify its
  pin count matches the package you intend (read the `.kicad_sym`, or use the MCP
  `get_component_pins`); a mismatch silently mis-maps the extra pins.
- If the kicad-sch-api MCP server is connected (see `.mcp.json`), you can confirm
  pin numbering for unfamiliar parts with its tools — e.g. `get_component_pins`,
  `find_pins_by_name`, `find_pins_by_type`. This is optional: if the server is
  not connected, rely on `find_symbol.py` and `main.py`'s pattern instead — a
  missing MCP server must not stop the loop.
- **Sourcing / availability (OPTIONAL — only when the user asks for real parts,
  a BOM, or sourcing, or supplies MPNs).** Check real stock/price:
  `PYTHONUTF8=1 uv run python tools/check_availability.py "<query>"`. **JLCPCB
  works without any credentials** (via the keyless tscircuit JLCSearch mirror,
  rows tagged `jlcpcb:jlcsearch`); DigiKey needs `DIGIKEY_CLIENT_ID`/`_SECRET`
  and is skipped otherwise. It never returns fake data and prints a
  `skipped: <source> -- <reason>` line for any source it could not query.
  - Record a `### Sourcing` table in the iteration-plan block with columns
    `| ref | MPN | source | stock | price | note |`.
  - **Honesty rule:** if a source was skipped (no credentials / network error),
    write "not checked — no credentials" in the note; **never invent stock or
    prices.** No creds at all → say sourcing was not verified and move on; this
    must not block the design.
  - Attach the chosen part's identity to its component as plain KiCad
    properties via kwargs — `Component(..., **{"MPN": "2N7000",
    "Manufacturer": "onsemi", "Distributor": "DigiKey"})`. They round-trip into
    the schematic (same mechanism as `Sim.*`); no schema change needed.

## Phase 3 — WRITE
<!-- language-coupled: this WRITE step teaches the circuit_synth DSL (@circuit / Net / generate_kicad_project). A future DSL swap repoints this section only; see workingdocs/design_considerations/loop-boundary-contract.md rule R3. -->
- Create/modify `circuit-synth/<snake_case_name>.py` following `main.py`'s
  pattern: `@circuit(name=...)`, `Net(...)` for connections (GND/VCC-style
  names auto-become power symbols), `component[pin] += net`.
- In `__main__`: `generate_kicad_project(project_name=..., generate_pcb=False)`.
  Do NOT call gerber functions (unavailable in this build).
- **Multi-sheet / hierarchical designs.** Split into sheets when the design has
  distinct functional blocks (power, MCU, analog front-end, ...), the user asks
  for it, or it exceeds ~15 components. Pattern: write one `@circuit` function
  per block, and a top `@circuit` that creates the *shared* nets and calls each
  block, **passing the same `Net` objects** into the blocks that must connect:

  ```python
  @circuit(name="psu")
  def psu(vin, v5, gnd): ...        # components here land on the psu sheet

  @circuit(name="amp")
  def amp(v5, gnd, sig_in, sig_out): ...

  @circuit(name="main")
  def main():
      vin, v5, gnd = Net("VIN_9V"), Net("V5"), Net("GND")
      sig_in, sig_out = Net("SIG_IN"), Net("SIG_OUT")
      psu(vin, v5, gnd)             # auto-registered as a child sheet
      amp(v5, gnd, sig_in, sig_out) # V5/GND shared by object identity
  ```

  Generation emits one `.kicad_sch` per block plus the root; a net shared
  between two or more blocks becomes a **sheet pin** on each (e.g. `V5`), while
  power nets (`GND`/`VCC*`) use global power symbols, not pins. A net used
  inside only one block stays local to that sheet — so to expose a block's I/O,
  share that net with the top or another block. See
  `tools/hierarchical_example.py` for a runnable two-sheet reference.
- Simulation flattens the hierarchy automatically; measure nodes by net name as
  usual (`result.get_voltage("V5")`) — no special handling needed.
<!-- /language-coupled -->

## Phase 4 — GENERATE
- Run: `PYTHONUTF8=1 uv run python circuit-synth/<name>.py`
<!-- language-coupled: the @circuit(name=)/project_name= file-naming rule is circuit_synth-specific. See workingdocs/design_considerations/loop-boundary-contract.md rule R3. -->
- **The generated `.kicad_sch`/`.kicad_pro` are named after `@circuit(name=...)`,
  NOT the `project_name=` folder** (issue #358). So a design with
  `@circuit(name="sipm_tia")` written by `generate_kicad_project(project_name=
  "SiPM_TIA")` produces `SiPM_TIA/sipm_tia.kicad_sch`. Point ERC / save-gate /
  sim script paths at the circuit name, not the folder name.
<!-- /language-coupled -->

- Then verify the output is real, not an empty shell:
  the emitted `.kicad_sch` must contain a `(symbol` block per component and a
  `(property "Reference" "<ref>"` for each expected reference. A schematic of
  ~1 KB with only a text box means every component silently failed.

**Error routing table:**
| Symptom | Route |
|---|---|
| `LibraryNotFound` / `Unknown library ID` | Phase 2 — fix that lib id |
| Schematic missing components / tiny file | Read the run log for `Failed to add component`; Phase 2 or 3 |
| Python exception in your file | Phase 3 — fix the code |
| `UnicodeEncodeError` | You forgot `PYTHONUTF8=1`; rerun |
| Gerber/PCB errors | Ignore — unavailable feature; ensure `generate_pcb=False` |

## Phase 4.5 — ERC (optional connectivity gate)
- Run KiCad's headless Electrical Rules Check to catch real wiring mistakes
  (undriven power, dangling pins) before trusting the schematic:
  `PYTHONUTF8=1 "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc
  --format json --severity-all --output erc.json <project>/<name>.kicad_sch`
  (netlist/ERC on the **root** sheet covers subsheets too).
- The generator's ERC gate runs **by default** (`erc_gate=True`): it iterates ERC +
  net-aware `PWR_FLAG` fixes for the common `power_pin_not_driven` case (a power pin
  with no driver — including a real part's power rails) and returns the residual
  report on the result (`result["erc_report"].summary()`). Pass `erc_gate=False` to
  skip it (e.g. when kicad-cli is absent and you want a faster run). Simple 2-pin
  local nets are also drawn as real wires by default (`selective_wires=True`), guarded
  by a netlist-equivalence check that reverts if a wire would change connectivity.
- Paste the ERC summary into `design_log.md`. Treat remaining **errors** as
  FAIL → route back to Phase 3 (fix the connection). **Warnings** like
  `isolated_pin_label` on an I/O net terminated by a single label are normal —
  note them, don't chase them. If kicad-cli is absent, skip this phase.
- **Save-crash gate.** ERC/netlist/PDF all *load* a schematic that KiCad's GUI
  would crash (segfault + truncate) when saving — so before trusting the file,
  reproduce a GUI save headlessly: **copy** the `.kicad_sch`, run
  `kicad-cli sch upgrade --force <copy>` on the copy, and require **all three**:
  `rc == 0` **AND** the copy is still `> 0` bytes **AND** it reloads
  (`kicad-cli sch erc <copy>` → 0 or 5). Traps that make this read a false
  "clean": never read the rc through a pipe (`… | tail; echo $?` reports tail's
  rc — a 139 segfault prints "0"); a crash can leave a **0-byte file at any rc**;
  and on Windows/Git-Bash never hand `kicad-cli.exe` an MSYS `/tmp/...` path (it
  silently writes 0 bytes, exit 0) — use project-relative paths. A `rc=139` here
  is a real corruption bug, not a warning.

### Recurring real-part ERC errors you must fix in the Python (the autofix won't)
The ERC-gate autofix only handles `power_pin_not_driven` (missing `PWR_FLAG`).
The errors below are **wiring decisions** on real ICs — the autofix (correctly)
won't guess them, so every real-part design must fix them in the Python source:
- **Exposed pads** (`EP`/`EPAD`/`PAD` pins) → connect explicitly: **GND** for
  regulators/converters, the **V− rail** for op-amps. Left floating they trip
  `pin_not_connected` / `power_pin_not_driven`.
- **Open-collector status pins** (`PGOOD`, `/FAULT`, …) → **pull up** to a rail
  (a resistor), or add a deliberate no-connect with a note.
- **Passive utility pins with no obvious net** (charge-pump `CP`/`C+`/`C-`,
  noise-reduction `NR`, `BYP`) → **bypass cap per datasheet**; flag
  "datasheet-verify" in the design log.
- **Bonded output+feedback pins** (ADA4817-style `FB` + `OUT`, both typed
  Output) → put the feedback network on **`FB`** and the load on **`OUT`**;
  tying them to one net is an ERC output-output conflict even though they're
  internally bonded.
- **Multi-voltage programming pins** (e.g. TPS7A4701 ANY-OUT bank) → **strap per
  datasheet** (grounded in external-FB mode); don't leave floating.
- **Multi-unit (dual/quad) parts** are placed as **one `Component`** and now
  simulate **per-unit automatically** — wire both halves on the same part; no
  need to split a dual into two singles.

## Phase 5 — SIMULATE
<!-- language-coupled: the .simulate() API and Sim.* model controls are circuit_synth-specific; the run/measure/plot/fallback *procedure* is portable. See workingdocs/design_considerations/loop-boundary-contract.md rule R3. -->
- **DC / operating point:** follow the working pattern in
  `tools/simulate_example.py` to run an operating-point analysis of your circuit
  and capture node voltages for every net named in the acceptance criteria. The
  pattern is: build the `@circuit` function, then `sim = circuit.simulate()`,
  `result = sim.operating_point()`, and read values with
  `result.get_voltage("NET_NAME")` (ngspice node lookup is case-insensitive, so
  `"VOUT_3V3"` and `"vout_3v3"` both work).
- **AC / frequency response:** follow `tools/simulate_filter.py`. Drive the input
  with a `Simulation_SPICE:VSIN` source (it carries an AC magnitude of 1 V, so the
  output node *is* the transfer function), then
  `result = sim.ac_analysis(start_hz, stop_hz, points)` and measure with
  `result.cutoff_frequency("NET")` (−3 dB corner), `result.passband_gain_db("NET")`,
  and `result.bode("NET")` → `(freq, magnitude_db, phase_deg)`. Roll-off is best
  measured on the asymptote (e.g. 10·fc → 100·fc), not fc → 10·fc (fc sits on the
  −3 dB knee).
- **Declaring sources:** use KiCad's real `Simulation_SPICE` symbols — `VDC` for a
  DC supply, `VSIN` for AC/transient stimulus. Pin 1 is `+`, pin 2 is `-`. Do NOT
  use `Device:V`/`Device:I` (not real KiCad symbols). An explicit source overrides
  the net-name rail heuristic on the nets it drives. That heuristic matches **whole
  net-name tokens**, not substrings (so `VINT_*`/`VMID_*` are not injected as a
  `VIN` supply), and logs every rail it injects — check the log if a node reads
  driven when you didn't declare a source for it.
- **Transient stimulus:** pass waveform parameters as component kwargs (they are
  stored as extra fields). `VSIN` reads `amplitude`/`frequency`/`offset`; `VPULSE`
  reads `v1`/`v2`/`td`/`tr`/`tf`/`pw`/`per`; `VPWL` reads `points` (a string or a
  list of `(t, v)` pairs). Keep SI suffixes (`1k`/`1m`/`1u`/`1n`) — ngspice parses
  them. Run with `sim.transient_analysis(step_s, end_s)`; an optional `options={...}`
  (e.g. `reltol`/`abstol`/`gmin`) tunes ngspice convergence on any analysis.
- **Transient initial conditions / UIC:** `transient_analysis` takes keyword-only
  `use_initial_condition=True` (emit `uic` — skip the DC op point; needed when a
  stiff/switcher model won't converge), `initial_conditions={"VOUT": 0}` (`.ic`
  node voltages — pass the **net name**, matched case-insensitively), `start_time`
  (discard the settling head) and `max_time` (cap the internal timestep). A
  soft-start run from a discharged output is
  `sim.transient_analysis(step_s, end_s, use_initial_condition=True, initial_conditions={"VOUT": 0})`.
  (`.nodeset` is not exposed — use `initial_conditions`.)
- **Active-device models (diodes/BJTs/MOSFETs):** naming a real part in `value`
  (e.g. `value="1N4148"`, `value="2N3904"`) pulls **datasheet-fit** parameters from
  the built-in model library when known; otherwise a device falls back to a
  textbook-generic model. The converter records which tier each device got in
  `sim.model_provenance[ref].tier` (`datasheet_fit` / `generic` / `vendor_lib`) and
  logs it, so a generic is never silently passed off as the real part. **Schottky
  rectifiers** (the usual PSU rectifier) are available by name: `value="SS14"` or
  `value="1N5819"` (datasheet-fit), or `value="DefaultSchottky"` (generic low-Vf).
  Naming a part the library can't resolve is a hard error — **unless** you also
  give `Sim.Params`, in which case it degrades to the kind's generic
  (`DefaultDiode`/`DefaultNPN`/`DefaultNMOS`) with your overrides applied and a
  warning (tier `generic`), so an unlisted part can be param-fitted
  (e.g. `value="SomeSchottky", Sim.Params="IS=1e-6 RS=0.05"`). **Diode terminals
  resolve by the symbol's A/K pin names, not pin order** — on `Device:D*` pin 1 is
  the cathode (K), so wire the symbol the way the schematic should read and the
  SPICE anode/cathode follow it automatically (no sim-only polarity flip needed).
- **Op-amps** default to an ideal VCVS (infinite gain-bandwidth), so feedback/source
  capacitance has no effect on simulated bandwidth or stability. For a bandwidth- or
  stability-sensitive design (e.g. a transimpedance amp with a large source cap) add
  `Sim.Gbw="1.4G"` to opt into a single-pole GBW-limited macromodel — then the Rf·Cf
  pole, source capacitance, and finite loop bandwidth interact, so cap-limited rolloff
  and gain peaking become visible. Without `Sim.Gbw` the ideal model is unchanged.
- **Linear regulators / LDOs** (a `Regulator_Linear:*` symbol, or any symbol with
  `Sim.Device="LDO"`) simulate as a datasheet-parameterized behavioral macromodel:
  the output regulates to `VOUT`, tracks `VIN-VDROP` in dropout, and draws `IQ` from
  the input. Give it `Sim.Params="vout=3.3 vdrop=0.3 rser=0.1 iq=2m"` (only `vout` is
  required — `vdrop` defaults 0.3 V, `rser` 0.05 Ω, `iq` 1 mA; a bare `m` means milli
  here). Alternatively name a ModelLibrary entry carrying a `VOUT` param via `value=`
  (tier `datasheet_fit`). The tier is recorded in `sim.model_provenance[ref]` and
  logged. **An LDO with no resolvable `VOUT` is a hard error** (a regulator's output
  cannot be guessed). **Limitation:** the macromodel has no current limit or thermal
  foldback — it will source unlimited current into a short, so don't use it to check
  overload/short-circuit protection.
- **Switching regulators (buck/boost)** (a `Regulator_Switching:*` symbol needs an
  explicit `Sim.Device="BUCK"` or `"BOOST"` — topology can't be guessed) simulate as a
  behavioral macromodel that replaces **only the IC**: the inductor, output cap, and
  feedback divider stay your real schematic parts, so BOM/ERC/sourcing stay truthful.
  Give it `Sim.Params="fsw=500k vout=3.3"` (both required; optional `vf` diode-drop
  default 0.45, `ron_hs` 0.1, `dmax` 0.95/0.9, `vramp` 1.0). Terminals resolve by pin
  name (SW/VIN/GND required, FB read but unused by v1). Run a **transient** with a fine
  step (`sim.transient_analysis(step_time=10e-9, end_time=1e-3)` — use ≤ 1/50 of the
  switching period, or PWM edges alias and inflate ripple). **This is an open-loop
  computed-duty model** (provenance `*_openloop`): it tracks line and gives correct
  steady-state output, ripple, and inductor stress, but has **no active load-step
  recovery** (a load step shows the passive LC settling), is **non-synchronous** (diode
  freewheel, so sync-rectifier efficiency is underestimated), and has **no current
  limit**. `.ac` on this cycle-accurate model is meaningless (a PWM comparator has no
  small-signal linearization — you'll get a warning); for loop-gain/phase-margin use
  the **averaged** model below. **Boost** relies on your external rectifier diode
  (SW→OUT) and inductor (VIN→SW), and needs `use_initial_condition=True` to converge
  (start `initial_conditions={"OUT": <vin>}`). **Flyback is supported — see the
  flyback bullet below.** Forward/half-bridge/LLC and **multi-winding transformers
  are not simulatable yet** — say so rather than approximating.
  - **Measuring a switching result** (`SimulationResult` helpers): `average(node)` /
    `ripple_pp(node)` over the steady-state tail; `settling_time(node, final=...)`;
    `branch_current("L1")` for inductor current (saturation margin — pass the
    schematic ref). Efficiency: `Pout ≈ average("OUT")**2 / Rload`, `Pin ≈
    average_power("VIN", "Vsource")` (mind the source's current sign).
  - **CCM test-load sizing (open-loop reads HIGH at light load):** the model is
    CCM-only, so a load light enough to push the inductor discontinuous reads
    3–15 % high. Size a sim-only test load (`in_bom=False`, so BOM/ERC stay
    truthful) to keep it continuous: inductor ripple `dI_pp = VIN·D/(L·fsw)`;
    require the input-referred average `I_in_avg ≈ VOUT·IOUT/(VIN·η) > dI_pp/2`.
    Confirm it in the result — `min(branch_current("L1"))` over the settled tail
    must stay > 0; a negative dip means DCM, so distrust the average (run 3: a
    guessed 680 Ω read +3–15 %, 300 Ω from this rule read −1.6 %).
  - **Seed the output IC for steady-state:** start `initial_conditions={"OUT": <≈vout>}`,
    not `<vin>` — from IC=Vin a boost output overshoots to ~1.4× target then bleeds
    down with `τ = Cout·Rload`, which usually outlasts a few-ms run, so the tail
    averages mid-decay. Keep IC=Vin only when the start-up transient itself is what
    you're measuring.
  - **Measurement windows:** take `ripple_pp` over the last few switching cycles
    (`start_time = t_end − 10/fsw`), not the default 20 % tail — that window still
    holds settling drift. Read inductor peak over the settled tail, **not** globally:
    the global max is the inrush spike (run 3 saw an 11 A inrush vs 0.42 A steady
    state), so a global L-peak overstates saturation stress ~26×.
- **Buck loop stability (averaged model + `.ac`)** — add `mode=avg` and a `vref`
  (the controller's internal reference the divider tap regulates to) to a **buck**'s
  `Sim.Params`, e.g. `Sim.Params="fsw=500k vout=3.3 vref=0.8 mode=avg"`. This swaps
  the cycle-accurate model for an **averaged (non-switching) voltage-mode** model — a
  gm-C error amp (`gm` default 1e-3, `cea` 1e-7, `rea` 1e6) + a continuous averaged
  PWM switch — which **linearizes under `.ac`**, so you get a real loop gain. Measure
  it by **voltage injection**: split the divider tap from the FB pin with a
  `Simulation_SPICE:VSIN` (defaults `ac=1`; set `amplitude="0" offset="0"` so it's a
  DC short), naming the divider-side net `FB_A` and the pin-side net `FB_B`:
  ```python
  # ...divider tap -> FB_A; VSIN FB_A->FB_B; U1 FB pin -> FB_B...
  res = sim.ac_analysis(start_freq=10, stop_freq=1e6, points=100)
  freq, mag_db, phase = res.loop_gain("FB_A", "FB_B")   # T = -V(FB_A)/V(FB_B)
  pm = res.phase_margin("FB_A", "FB_B")   # deg, or None if no 0 dB crossing
  gm = res.gain_margin("FB_A", "FB_B")    # dB,  or None if phase never hits -180
  ```
  Raising `cea` slows the loop (lower crossover, more phase margin). **Validity:** CCM
  voltage-mode buck only; results above ~FSW/2 are not physical (averaging breaks);
  the plain type-I integrator has no phase boost, so a stable design keeps its
  crossover well below the LC resonance. For a quick stability *proxy* without the
  averaged model, the cycle model's load-step transient (a `PWL` current load) shows
  ringing/settling — use that when you only need "does it ring", not exact margins.
- **Transformers / coupled inductors** — a `Device:Transformer_1P_1S` symbol (or any
  symbol with `Sim.Device="TRANSFORMER"`) simulates as two coupled inductors + a SPICE
  `K` element. Give it `Sim.Params="lp=100u n=0.5"` (`lp` = primary inductance,
  required; `n` = turns ratio Ns/Np, or an explicit `ls`; `k` coupling default 0.999,
  must be in (0,1]). **Polarity follows the symbol's printed dots** (AA on the
  primary, SA on the secondary) — a flyback ties the secondary dot SA to the
  secondary return and feeds the rectifier from SB. Winding currents:
  `branch_current("T1_P")` / `("T1_S")`. **Simulation caveat:** SPICE needs a DC path
  from every node to ground, so tie the isolated secondary's return to the sim's GND
  net (or bridge it with a large resistor) — this is a simulation artifact, not a
  design change. Lower `k` (leakage) is realistic but makes transients slow and
  spiky; `k=1` is the fast idealization.
- **Flyback converters** — `Sim.Device="FLYBACK"` on the controller IC emits the
  open-loop computed-duty macromodel (CCM duty `D=(VOUT+VF)/((VOUT+VF)+N·VIN)`) with
  a **low-side switch** and a **drain avalanche clamp** (`vclamp` default 150 V — set
  it to the IC's rating, e.g. 650 for offline parts; it bounds the leakage spike the
  way a real integrated switch does). `Sim.Params="fsw=100k vout=5 n=0.5"` — `n` is
  the transformer turns ratio Ns/Np and is **required** (it can't be read from the
  separate transformer part; keep it equal to the transformer's `n`). Wiring: primary
  dot AA→VIN, AB→the IC's SW pin; secondary dot SA→secondary return, SB→rectifier
  anode; use a Schottky rectifier (`Sim.Params="IS=1e-6"` on a `Device:D`) so the
  real diode drop matches the model's `vf`≈0.45 correction. Runs need
  `use_initial_condition=True, initial_conditions={"OUT": 0}` (no DC op point for
  open-loop PWM) and a step ≤ 1/50 of the switching period. **Limitations:** CCM duty
  formula (light-load/DCM reads high), open loop (no load-step recovery),
  non-synchronous, no current limit; clamp dissipation modeled but not reported.
- **Simulation-only model controls (KiCad `Sim.*`, passed as component kwargs):**
  `Sim.Enable="0"` excludes a part from simulation (its symbol/footprint stay put —
  use it for connectors/test points so `validate()` doesn't flag them);
  `Sim.Params="bf=250 vaf=80"` overrides model params; `Sim.Library="path.lib"` +
  `Sim.Name="MODEL"` (+ optional `Sim.Pins="1=out 2=inp 3=inn"`) attaches an external
  vendor `.lib`/`.subckt` model verbatim, and if that subckt takes parameters
  `Sim.Params="gain=3 fsw=500k"` passes them on the instance line. Pass dotted names as
  `Component(..., **{"Sim.Enable": "0"})`.
- **Vendor PSpice/LTspice model dialect:** most vendor `.lib` files (e.g. TI's
  unencrypted PSpice models) use idioms ngspice rejects by default (`PARAMS:`,
  `VALUE={IF(...)}`). Run them with `circuit.simulate(compat="psa").operating_point()`
  (`psa` = PSpice + whole-netlist; also `lt`/`ltps`/`a` etc.), or put `Sim.Compat="psa"`
  on the schematic next to the `Sim.Library` that needs it. Without it such a model
  errors on load. Encrypted vendor models (`.enc`) can't be used by ngspice at all.
- **Keeping a part out of the BOM (KiCad `in_bom`):** `Sim.Enable="0"` is *not* a BOM
  control — a real part can be sim-disabled yet still belong in the BOM. Two BOM
  exclusions apply automatically: `Simulation_SPICE:*` stimulus symbols (voltage/
  current sources) are never BOM parts, and any component whose value is DNP is
  dropped. For a **model-only passive** that has no physical part (e.g. a device's
  internal terminal capacitance you add just so the sim sees it), pass
  `Component(..., in_bom=False)` to emit KiCad's native `(in_bom no)` so
  `generate_bom()` omits it. `generate_bom()` also auto-adds any attached
  `MPN`/`Manufacturer`/`Distributor`/`LCSC` columns — no `fields=` needed.
- On Windows the ngspice DLL bundled with KiCad is auto-configured — no separate
  ngspice install is needed.
- **Save a plot of the result** so the log is visual, not just numbers. Every
  `SimulationResult` has headless PNG savers (no display needed):
  `result.save_bode_plot("sim_plots/iterN_<name>_bode.png", "NET")` for AC,
  `result.save_transient_plot("sim_plots/iterN_<name>_tran.png", ["NET", ...])`
  for transient, `result.save_dc_transfer_plot("sim_plots/iterN_<name>_dc.png",
  "NET", sweep_label="Vin")` for a DC sweep. Write them under a `sim_plots/`
  directory in the project root (created automatically); use the iteration
  number and circuit name in the filename so they don't collide. They return
  the written path, or `None` if plotting is unavailable — if `None`, skip the
  embed step, don't fail the loop.
- If simulation errors out or the backend is unavailable (the helper prints
  `SIMULATION_UNAVAILABLE` and exits 2): fall back to STATIC verification —
  recompute expected values by hand (Ohm's law, divider ratios), confirm net
  connectivity in the `.kicad_sch`, and mark the iteration
  "**not simulation-verified**" in `design_log.md`. Never fabricate measurements.
<!-- /language-coupled -->

## Phase 6 — EXAMINE & DECIDE
- Compare each measurement to its criterion → PASS/FAIL table in `design_log.md`.
- **Embed the plot(s)** you saved in Phase 5: after the PASS/FAIL table, add one
  markdown image per plot — `![iter N bode](sim_plots/iterN_<name>_bode.png)` —
  followed by a one-line reading of what it shows (e.g. "−3 dB at ~9.7 kHz,
  −20 dB/dec rolloff — matches the 1st-order target"). If a plot save returned
  `None` (plotting unavailable), skip the embed and note "plot unavailable"; if
  simulation didn't run at all, there is no plot — say so, never invent one.
- All PASS → **COMPLETE**: summarize (files written, final values, how verified,
  path to the `.kicad_pro` to open in KiCad). Stop.
- Any FAIL → diagnose before looping:
  - Values wrong but topology right (e.g. Vout off by a ratio) → Phase 3,
    adjust component values; show the algebra in the log.
  - Topology wrong (missing path, shorted net, wrong pin) → Phase 1, re-plan.
  - Same failure twice in a row → change strategy, don't repeat the edit.
- Iteration 5 still failing → stop; report best attempt, remaining gaps, and
  what a human should look at. An honest partial beats a false success.

## Editing an existing design

Use this when the user asks to modify a circuit that already has a
`circuit-synth/*.py` source in this project. The design's **source of truth is
the Python file**, not the `.kicad_sch` — every downstream step (simulation,
`Sim.*` model controls, `validate()`, sourcing/BOM) reads the Python circuit, so
edits must go there. In-place edits to the generated `.kicad_sch` are invisible
to those steps and are **overwritten the next time the project is regenerated**.

<!-- language-coupled: the edit steps operate on the circuit_synth Python source (generate_kicad_project / force_regenerate update mode). See workingdocs/design_considerations/loop-boundary-contract.md rule R3. -->
1. **Locate the source.** Find the `circuit-synth/*.py` whose
   `generate_kicad_project(project_name=...)` matches the project the user means
   (usually `main.py` or the one named after the target). If several could
   match, ask which; never guess and hand-edit the `.kicad_sch`.
2. **Change the Python.** Make the requested edit in code — component values,
   added/removed components, net connections, `Sim.*` kwargs, MPN/Manufacturer
   kwargs. Follow the same API patterns as the rest of the file.
3. **Regenerate in update mode (placement-preserving).** Re-run the file:
   `PYTHONUTF8=1 uv run python circuit-synth/<name>.py`. Keep the default
   `generate_kicad_project(..., generate_pcb=False)` — its default
   `force_regenerate=False` performs an **update**: components are matched by
   UUID/reference/topology, so existing parts keep their manual KiCad placement
   while your change is applied and any new part is dropped in a free column to
   the right (reposition later in KiCad). **Do not pass `force_regenerate=True`**
   unless the user explicitly accepts losing all manual placement — it rewrites
   the schematic from scratch. Verify the edit landed the same way Phase 4 does
   (the changed value / new `(symbol` block is present in the `.kicad_sch`).
4. **Re-simulate and re-examine (Phases 5–6)** for the criteria the edit
   affects. Append a new block to `design_log.md` headed
   `## Iteration N — edit`: state what the user asked, the code change, the
   regeneration result (updated/preserved/added), the new measurements vs. the
   criteria (PASS/FAIL), and an embedded plot if you produced one.
5. **Iterate** as in Phase 6 if the edit didn't meet its criterion.
<!-- /language-coupled -->

**MCP boundary.** The kicad-sch-api MCP server (if connected) stays a
**read-only helper** in this loop — pin lookups (`get_component_pins`,
`find_pins_by_name`) during Phase 2. Its editing tools (`add_component`,
`add_wire`, `bulk_update_components`, …) directly mutate a `.kicad_sch`; on a
project that has a circuit-synth `.py` source, those edits diverge from the
source and are lost on the next regeneration, so **route every value/topology
change back to the Python file**. The MCP editing tools are for schematics that
have **no** circuit-synth source (foreign/hand-drawn `.kicad_sch`), which this
skill does not manage.
