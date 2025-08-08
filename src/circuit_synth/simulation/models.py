"""
SPICE Model Library for Circuit-Synth Simulation

This module provides a comprehensive library of SPICE models for common components.
Models are sourced from:
1. Standard SPICE model parameters
2. Manufacturer datasheets
3. LTspice and ngspice default models
4. Industry-standard approximations

The models are organized by component type and can be used directly in simulations
or customized for specific requirements.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SpiceModel:
    """Container for SPICE model parameters."""

    name: str
    model_type: str  # D, NPN, PNP, NMOS, PMOS, etc.
    parameters: Dict[str, float]
    description: str = ""
    manufacturer: str = ""
    datasheet_url: str = ""


class ModelLibrary:
    """SPICE model library for circuit-synth simulations."""

    def __init__(self):
        self.models = {}
        self._load_default_models()

    def _load_default_models(self):
        """Load default SPICE models for common components."""

        # Diode Models
        self.models["1N4148"] = SpiceModel(
            name="1N4148",
            model_type="D",
            parameters={
                "IS": 2.52e-9,  # Saturation current
                "RS": 0.568,  # Series resistance
                "N": 1.752,  # Emission coefficient
                "TT": 4e-9,  # Transit time
                "CJO": 4e-12,  # Zero-bias junction capacitance
                "VJ": 0.7,  # Junction potential
                "M": 0.333,  # Grading coefficient
                "BV": 100,  # Reverse breakdown voltage
                "IBV": 0.1e-3,  # Current at breakdown
            },
            description="Fast switching diode",
            manufacturer="Various",
        )

        self.models["1N4007"] = SpiceModel(
            name="1N4007",
            model_type="D",
            parameters={
                "IS": 7.02e-9,
                "RS": 0.0341,
                "N": 1.8,
                "TT": 4.32e-6,
                "CJO": 18.5e-12,
                "VJ": 0.75,
                "M": 0.333,
                "BV": 1000,
                "IBV": 5e-6,
            },
            description="1A 1000V rectifier diode",
            manufacturer="Various",
        )

        self.models["LED_Red"] = SpiceModel(
            name="LED_Red",
            model_type="D",
            parameters={
                "IS": 1e-20,
                "RS": 2.5,
                "N": 1.5,
                "BV": 5,
                "IBV": 10e-6,
            },
            description="Red LED (Vf ~1.8V)",
        )

        # BJT Transistor Models
        self.models["2N3904"] = SpiceModel(
            name="2N3904",
            model_type="NPN",
            parameters={
                "IS": 6.734e-15,  # Saturation current
                "BF": 416.4,  # Forward current gain
                "NF": 1,  # Forward emission coefficient
                "VAF": 74.03,  # Forward Early voltage
                "IKF": 0.06678,  # Forward knee current
                "ISE": 6.734e-15,  # B-E leakage saturation current
                "NE": 1.259,  # B-E leakage emission coefficient
                "BR": 0.7371,  # Reverse current gain
                "NR": 1,  # Reverse emission coefficient
                "VAR": 50,  # Reverse Early voltage
                "RB": 10,  # Base resistance
                "RC": 1,  # Collector resistance
                "RE": 0.1,  # Emitter resistance
                "CJE": 4.493e-12,  # B-E zero-bias capacitance
                "CJC": 3.638e-12,  # B-C zero-bias capacitance
                "TF": 301.2e-12,  # Forward transit time
                "TR": 239.5e-9,  # Reverse transit time
            },
            description="General purpose NPN transistor",
            manufacturer="Various",
        )

        self.models["2N3906"] = SpiceModel(
            name="2N3906",
            model_type="PNP",
            parameters={
                "IS": 1.41e-15,
                "BF": 180.7,
                "NF": 1,
                "VAF": 35.99,
                "IKF": 0.08,
                "ISE": 3.31e-15,
                "NE": 1.5,
                "BR": 4.977,
                "NR": 1,
                "VAR": 50,
                "RB": 20,
                "RC": 2,
                "RE": 0.2,
                "CJE": 8.504e-12,
                "CJC": 4.962e-12,
                "TF": 466.5e-12,
                "TR": 51.35e-9,
            },
            description="General purpose PNP transistor",
            manufacturer="Various",
        )

        self.models["BC547"] = SpiceModel(
            name="BC547",
            model_type="NPN",
            parameters={
                "IS": 13.0e-15,
                "BF": 400,
                "NF": 1,
                "VAF": 100,
                "IKF": 0.1,
                "ISE": 2e-15,
                "NE": 1.5,
                "BR": 1,
                "NR": 1,
                "VAR": 50,
                "RB": 200,
                "RC": 3,
                "RE": 0.5,
                "CJE": 10e-12,
                "CJC": 3e-12,
                "TF": 0.4e-9,
                "TR": 50e-9,
            },
            description="Low noise NPN transistor",
            manufacturer="Various",
        )

        # MOSFET Models
        self.models["2N7000"] = SpiceModel(
            name="2N7000",
            model_type="NMOS",
            parameters={
                "VTO": 1.8,  # Threshold voltage
                "KP": 0.24,  # Transconductance parameter
                "GAMMA": 0.37,  # Body effect parameter
                "PHI": 0.65,  # Surface potential
                "LAMBDA": 0.01,  # Channel length modulation
                "RD": 1,  # Drain resistance
                "RS": 0.5,  # Source resistance
                "CBD": 35e-12,  # B-D junction capacitance
                "CBS": 35e-12,  # B-S junction capacitance
                "IS": 1e-14,  # Bulk junction saturation current
                "PB": 0.8,  # Bulk junction potential
                "CGSO": 88e-12,  # Gate-source overlap capacitance
                "CGDO": 88e-12,  # Gate-drain overlap capacitance
                "CGBO": 200e-12,  # Gate-bulk overlap capacitance
                "TOX": 100e-9,  # Oxide thickness
                "LD": 0.016e-6,  # Lateral diffusion
                "UO": 600,  # Surface mobility
                "W": 1e-3,  # Channel width
                "L": 2e-6,  # Channel length
            },
            description="N-channel enhancement mode MOSFET",
            manufacturer="Various",
        )

        self.models["BS250"] = SpiceModel(
            name="BS250",
            model_type="PMOS",
            parameters={
                "VTO": -3.0,
                "KP": 0.12,
                "GAMMA": 0.4,
                "PHI": 0.65,
                "LAMBDA": 0.02,
                "RD": 2,
                "RS": 1,
                "CBD": 40e-12,
                "CBS": 40e-12,
                "IS": 1e-14,
                "PB": 0.8,
                "CGSO": 100e-12,
                "CGDO": 100e-12,
                "CGBO": 250e-12,
                "TOX": 100e-9,
                "LD": 0.016e-6,
                "UO": 200,
                "W": 1e-3,
                "L": 2e-6,
            },
            description="P-channel enhancement mode MOSFET",
            manufacturer="Various",
        )

        self.models["IRF540"] = SpiceModel(
            name="IRF540",
            model_type="NMOS",
            parameters={
                "VTO": 3.9,
                "KP": 20,
                "GAMMA": 0.5,
                "PHI": 0.65,
                "LAMBDA": 0.001,
                "RD": 0.044,
                "RS": 0.01,
                "CBD": 1600e-12,
                "CBS": 1600e-12,
                "IS": 1e-14,
                "PB": 0.8,
                "CGSO": 1400e-12,
                "CGDO": 1400e-12,
                "CGBO": 3000e-12,
                "W": 0.68,
                "L": 2e-6,
            },
            description="Power MOSFET, 100V 33A",
            manufacturer="International Rectifier",
        )

        # Default/Generic Models
        self.models["DefaultDiode"] = SpiceModel(
            name="DefaultDiode",
            model_type="D",
            parameters={
                "IS": 1e-14,
                "RS": 0.1,
                "N": 1,
                "BV": 50,
                "IBV": 1e-3,
            },
            description="Generic silicon diode",
        )

        self.models["DefaultNPN"] = SpiceModel(
            name="DefaultNPN",
            model_type="NPN",
            parameters={
                "IS": 1e-14,
                "BF": 100,
                "BR": 1,
                "RB": 100,
                "RC": 10,
                "RE": 1,
            },
            description="Generic NPN transistor",
        )

        self.models["DefaultPNP"] = SpiceModel(
            name="DefaultPNP",
            model_type="PNP",
            parameters={
                "IS": 1e-14,
                "BF": 100,
                "BR": 1,
                "RB": 100,
                "RC": 10,
                "RE": 1,
            },
            description="Generic PNP transistor",
        )

        self.models["DefaultNMOS"] = SpiceModel(
            name="DefaultNMOS",
            model_type="NMOS",
            parameters={
                "VTO": 2.0,
                "KP": 0.1,
                "LAMBDA": 0.01,
                "W": 1e-3,
                "L": 10e-6,
            },
            description="Generic N-channel MOSFET",
        )

        self.models["DefaultPMOS"] = SpiceModel(
            name="DefaultPMOS",
            model_type="PMOS",
            parameters={
                "VTO": -2.0,
                "KP": 0.05,
                "LAMBDA": 0.01,
                "W": 1e-3,
                "L": 10e-6,
            },
            description="Generic P-channel MOSFET",
        )

    def get_model(self, name: str) -> Optional[SpiceModel]:
        """Get a SPICE model by name."""
        return self.models.get(name)

    def add_model(self, model: SpiceModel):
        """Add a custom SPICE model to the library."""
        self.models[model.name] = model
        logger.info(f"Added SPICE model: {model.name}")

    def list_models(self) -> Dict[str, str]:
        """List all available models with descriptions."""
        return {name: model.description for name, model in self.models.items()}

    def generate_spice_model_card(self, model_name: str) -> str:
        """Generate a SPICE .MODEL card for a given model."""
        model = self.get_model(model_name)
        if not model:
            return f"* Model {model_name} not found"

        # Format parameters for SPICE
        params = " ".join([f"{k}={v}" for k, v in model.parameters.items()])
        return f".MODEL {model.name} {model.model_type} ({params})"

    def apply_to_circuit(self, spice_circuit):
        """Apply all required models to a PySpice circuit."""
        # This would be called by the converter to add model definitions
        # to the SPICE netlist
        pass


# Global model library instance
MODEL_LIBRARY = ModelLibrary()


def get_model_library() -> ModelLibrary:
    """Get the global model library instance."""
    return MODEL_LIBRARY


# Example: How to add manufacturer-specific models
def load_manufacturer_models():
    """Example of loading manufacturer-specific SPICE models."""

    # TI Op-Amp Models
    MODEL_LIBRARY.add_model(
        SpiceModel(
            name="LM358",
            model_type="OPAMP",
            parameters={
                "GAIN": 100000,
                "RIN": 2e6,
                "ROUT": 75,
                "GBW": 1e6,  # Gain-bandwidth product
                "SR": 0.5e6,  # Slew rate V/s
            },
            description="Dual operational amplifier",
            manufacturer="Texas Instruments",
            datasheet_url="https://www.ti.com/lit/ds/symlink/lm358.pdf",
        )
    )

    # STMicroelectronics Models
    MODEL_LIBRARY.add_model(
        SpiceModel(
            name="STM32_GPIO",
            model_type="DIGITAL",
            parameters={
                "VOH": 3.3,
                "VOL": 0,
                "IOH": 20e-3,
                "IOL": 20e-3,
                "CIN": 5e-12,
            },
            description="STM32 GPIO pin model",
            manufacturer="STMicroelectronics",
        )
    )


# Resources for finding SPICE models:
SPICE_MODEL_SOURCES = """
SPICE Model Sources for Circuit-Synth Users:

1. **Manufacturer Websites** (Most accurate):
   - Texas Instruments: https://www.ti.com/design-resources/simulation-models
   - Analog Devices: https://www.analog.com/en/design-center/simulation-models
   - ON Semiconductor: https://www.onsemi.com/support/design-resources/models-simulations
   - STMicroelectronics: https://www.st.com/content/st_com/en/support/resources/cad-resources
   - Infineon: https://www.infineon.com/cms/en/product/promopages/spice-models/

2. **SPICE Software Libraries**:
   - LTspice: Built-in models (C:\\Program Files\\LTC\\LTspiceXVII\\lib\\)
   - ngspice: Standard library (/usr/share/ngspice/scripts/spinit)
   - PSpice: Model library (extensive but proprietary)

3. **Online Databases**:
   - https://www.centralsemi.com/spice_models
   - http://www.intusoft.com/models.php
   - https://www.diodes.com/design/tools/spice-models/

4. **Component Distributors**:
   - DigiKey: Often links to manufacturer SPICE models
   - Mouser: Includes SPICE model links in datasheets
   - Element14: Provides model downloads

5. **Creating Custom Models**:
   - Extract from datasheet parameters
   - Use parameter extraction tools
   - Measure actual components
   - Use circuit-synth's ModelLibrary.add_model()

6. **Model Formats**:
   - .MODEL statements (simple parameters)
   - .SUBCKT (subcircuit definitions)
   - Encrypted models (.inc files)
   - IBIS models (for high-speed digital)
"""


def print_model_sources():
    """Print information about where to find SPICE models."""
    print(SPICE_MODEL_SOURCES)
