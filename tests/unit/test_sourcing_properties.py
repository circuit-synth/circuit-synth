"""Sourcing properties on components (Stage 10.4).

MPN / Manufacturer / Distributor are attached as plain KiCad-style properties
via kwargs (no dedicated schema field) and must survive the circuit-synth
dict round-trip -- the same mechanism the Sim.* layer uses (Stage 9.1). This
lets the design loop annotate chosen parts with sourcing metadata without any
serialization changes.
"""

from circuit_synth import Component
from circuit_synth.core.component import Component as _Component


def test_sourcing_properties_accepted_and_roundtrip():
    c = Component(
        symbol="Device:R",
        ref="RSRC1",
        value="10k",
        **{
            "MPN": "RC0603FR-0710KL",
            "Manufacturer": "YAGEO",
            "Distributor": "DigiKey",
        },
    )
    assert getattr(c, "MPN") == "RC0603FR-0710KL"
    assert c._extra_fields["Manufacturer"] == "YAGEO"

    data = c.to_dict()
    data["ref"] = "RSRC2"  # distinct ref avoids the reference-registry collision
    revived = _Component.from_dict(data)
    assert revived._extra_fields.get("MPN") == "RC0603FR-0710KL"
    assert revived._extra_fields.get("Manufacturer") == "YAGEO"
    assert revived._extra_fields.get("Distributor") == "DigiKey"
