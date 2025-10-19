# PRD: Orthogonal Routing Support (Basic Implementation)

**Status:** Draft - Simplified for MVP
**Created:** 2025-10-19
**Updated:** 2025-10-19 (simplified scope)
**Branch:** `feature/orthogonal-routing`
**Related Issue:** [#195](https://github.com/circuit-synth/circuit-synth/issues/195)

## Overview

Add **basic** support for orthogonal (Manhattan) routing to circuit-synth. This implementation uses **orthogonal routing + blind/buried vias** to make routing as easy as possible.

**Key Strategy:** Orthogonal routing with blind/buried vias enabled by default provides:
- Simple 90° geometry (easier to route)
- Flexible layer transitions (blind/buried vias connect any two layers)
- Easy routing for complex boards

## MVP Goals

1. Enable orthogonal routing with blind/buried vias by default
2. Configure Freerouting for orthogonal routing with blind/buried support
3. Set KiCad design rules to enforce orthogonal constraints
4. Optional via size specification (default: 0.6/0.3 for reliability)
5. Simple API: `routing_style="orthogonal"` parameter
6. Maintain full backward compatibility

## Out of Scope (for MVP)

- Force-directed placement improvements → [#222](https://github.com/circuit-synth/circuit-synth/issues/222)
- Net-tie insertion → [#223](https://github.com/circuit-synth/circuit-synth/issues/223)
- Auto board outline → [#224](https://github.com/circuit-synth/circuit-synth/issues/224)
- DRC validation → [#225](https://github.com/circuit-synth/circuit-synth/issues/225)
- Custom Python auto-router (future work)
- Per-layer routing control (future work)
- Cost estimation (future work)
- Advanced trace width optimization (future work)

## Requirements (MVP)

### FR1: Basic API Parameter
- Add `routing_style` parameter to `generate_pcb()`
- Support: `"orthogonal"` or `None` (default)
- **When `routing_style="orthogonal"`, automatically enable blind/buried vias**
- Keep it simple - just a string parameter

```python
circuit.generate_pcb(
    routing_style="orthogonal"  # Enable orthogonal + blind/buried vias
)
```

### FR2: Via Size with Smart Defaults
- Add optional `via_size` parameter
- Format: `"drill_mm/annular_mm"` (e.g., `"0.6/0.3"`)
- **Default for orthogonal routing: `"0.6/0.3"`** (larger, more reliable vias from #195)
- If not specified with non-orthogonal routing, use KiCad defaults

```python
circuit.generate_pcb(
    routing_style="orthogonal",
    via_size="0.6/0.3"  # Optional - defaults to this for orthogonal
)
```

### FR3: Freerouting Configuration
- When `routing_style="orthogonal"`, configure Freerouting DSN to:
  - Disable 45° routing
  - Enforce 90° angles only
  - **Enable blind/buried vias** (allows any layer-to-layer connections)
  - Apply via size (default 0.6/0.3)

### FR4: KiCad Design Rules
- When `routing_style="orthogonal"`, set KiCad design rules to:
  - Restrict to orthogonal routing
  - **Enable blind/buried vias** in layer stackup
  - Set via sizes (default 0.6/0.3)
  - Basic clearance rules

### Non-Functional Requirements

#### NFR1: Backward Compatibility
- Existing code must work without changes
- Default behavior unchanged (`routing_style=None` → mixed routing)
- No deprecation warnings for existing patterns

#### NFR2: Documentation
- API documentation for new parameters
- Tutorial on orthogonal routing benefits
- Manufacturing guidelines (JLCPCB, OSH Park)
- Migration guide from diagonal to orthogonal

#### NFR3: Performance
- No significant performance impact on generation time
- Freerouting configuration should not slow down exports

## User Stories

### US1: Production-Ready PCBs
**As a** hardware engineer
**I want** to generate PCBs with orthogonal routing
**So that** my boards are cheaper to manufacture and more reliable

**Acceptance Criteria:**
- Can specify `routing_style="orthogonal"` in PCB generation
- Generated design rules enforce orthogonal routing
- Freerouting (if used) respects orthogonal constraints

### US2: Custom Via Sizes
**As a** PCB designer
**I want** to control via sizes independently of routing style
**So that** I can optimize for different manufacturing processes

**Acceptance Criteria:**
- Can specify `via_size="0.6/0.3"` separately from routing style
- Via sizes are applied to KiCad design rules
- Freerouting uses specified via sizes

### US3: Manual Routing Guidance
**As a** designer who routes manually
**I want** orthogonal routing constraints in my KiCad project
**So that** I follow best practices without auto-routing

**Acceptance Criteria:**
- Design rules prevent diagonal routing
- Via size constraints are set correctly
- DRC catches non-orthogonal traces

## Technical Design (Minimal)

### Simple API Addition

```python
# circuit_synth/circuit.py

class Circuit:
    def generate_pcb(
        self,
        routing_style: str | None = None,  # "orthogonal" or None
        via_size: str | None = None,        # "drill/annular" e.g. "0.6/0.3"
        **kwargs
    ):
        """Generate PCB with optional routing constraints

        When routing_style="orthogonal":
        - Enables 90° only routing (no diagonals)
        - Enables blind/buried vias for easy layer transitions
        - Defaults to 0.6/0.3 via size (larger, more reliable)
        """
        # If routing_style == "orthogonal":
        #   - Enable blind/buried vias
        #   - Set via_size to "0.6/0.3" if not specified
        #   - Configure Freerouting for orthogonal + blind/buried
        #   - Set KiCad design rules for orthogonal + blind/buried
        # If via_size provided:
        #   - Parse and apply to both Freerouting and KiCad
```

### Implementation Notes

- **No new modules needed** - just add parameters to existing methods
- **Orthogonal = blind/buried enabled** - this makes routing much easier
- **Smart defaults**: via_size defaults to "0.6/0.3" for orthogonal routing
- **Parse via_size**: Split on "/" to get drill and annular ring
- **Freerouting config**: Modify DSN export to:
  - Disable diagonal routing
  - Enable blind/buried vias
  - Set via sizes
- **KiCad rules**: Update .kicad_pro file with:
  - Orthogonal constraints
  - Blind/buried via enabled stackup
  - Via sizes
- **Keep it simple**: No complex data structures, just string parameters

### Implementation (Simplified)

#### Step 1: Add Parameters
- [ ] Add `routing_style` and `via_size` to `generate_pcb()` signature
- [ ] Parse and validate parameters

#### Step 2: Freerouting Integration
- [ ] Locate Freerouting DSN export code
- [ ] When `routing_style="orthogonal"`:
  - [ ] Disable 45° routing
  - [ ] Enable blind/buried vias
  - [ ] Set via size (default "0.6/0.3")

#### Step 3: KiCad Design Rules
- [ ] Find KiCad project file generation code
- [ ] When `routing_style="orthogonal"`:
  - [ ] Set orthogonal routing design rules
  - [ ] Enable blind/buried vias in stackup
  - [ ] Set via sizes (default "0.6/0.3")

#### Step 4: Basic Testing
- [ ] Create simple test circuit (MCU + a few components)
- [ ] Generate with `routing_style="orthogonal"`
- [ ] Verify Freerouting produces orthogonal routes
- [ ] Verify KiCad design rules are set correctly
- [ ] Try on existing example circuit (optional)

## Testing Strategy

### Unit Tests
- `RoutingConfig` serialization/deserialization
- `ViaSpec` parsing and calculations
- KiCad rule generation
- Freerouting rule generation

### Integration Tests
- Generate PCB with orthogonal routing
- Verify KiCad design rules applied
- Export to Freerouting and verify DSN
- Check DRC passes with orthogonal traces

### Example Projects
- Simple 2-layer board (orthogonal)
- 4-layer board with blind/buried vias
- Comparison: diagonal vs orthogonal routing
- Manufacturing cost analysis

## Success Metrics

- [ ] API available and documented
- [ ] Freerouting produces orthogonal routes
- [ ] KiCad design rules enforce orthogonal routing
- [ ] Manual routing DRC works correctly
- [ ] Zero breaking changes to existing code
- [ ] Tutorial and examples published
- [ ] Issue #195 resolved

## Open Questions

~~1. **Trace width optimization**: Should we also provide recommended trace widths for orthogonal routing?~~ ✅ **RESOLVED:** Provide recommended defaults, allow override
~~2. **Layer-specific rules**: Do we need different routing styles per layer (e.g., orthogonal on signal layers, any angle on power)?~~ ✅ **RESOLVED:** Board-wide setting for simplicity
3. **Auto-detection**: Should we analyze circuit complexity and suggest orthogonal vs mixed? (Future enhancement)
~~4. **Cost estimation**: Should we integrate manufacturing cost estimates based on routing choices?~~ ✅ **RESOLVED:** Provide guidelines in documentation, no automatic calculation

## Dependencies

- KiCad 9.0+ (for design rule format)
- Freerouting 1.9+ (for orthogonal routing support)
- kicad-sch-api (for project file manipulation)

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Freerouting doesn't respect orthogonal constraints | High | Low | Test early, fallback to manual rules |
| KiCad design rule format changes | Medium | Low | Version detection, format compatibility layer |
| Performance degradation with complex boards | Medium | Medium | Benchmark, optimize rule generation |
| User confusion about when to use orthogonal | Low | Medium | Clear documentation, examples, guidelines |

## Future Enhancements

- Custom Python auto-router with orthogonal-first algorithm
- AI-based routing style selection based on circuit type
- Cost/performance optimizer for routing decisions
- Visual routing preview before generation
- Impedance-controlled orthogonal routing for high-speed signals

---

**Decision Log:**

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-19 | Opt-in via parameter | Maintains backward compatibility, allows gradual adoption |
| 2025-10-19 | Separate via_size parameter | Provides flexibility, users may want large vias without orthogonal routing |
| 2025-10-19 | Prioritize Freerouting + manual rules | Freerouting already integrated, manual rules needed for non-auto-router users |
| 2025-10-19 | Full backward compatibility | Critical for production systems, no breaking changes allowed |
| 2025-10-19 | Orthogonal = blind/buried enabled | Makes routing much easier, key insight from #195 |
| 2025-10-19 | Default via size 0.6/0.3 for orthogonal | Larger vias are more reliable and cost-effective |
| 2025-10-19 | Board-wide routing style | Single routing style for all layers, simpler UX |
| 2025-10-19 | Cost info in docs only | Document cost implications, no automatic calculation in v1 |
