"""Custom JSON encoder for Circuit Synth types."""

import json
from enum import Enum


class CircuitSynthJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Circuit Synth specific types."""

    def default(self, obj):
        # Handle Enum types (like PinType)
        if isinstance(obj, Enum):
            return obj.value

        # Handle objects with to_dict method
        if hasattr(obj, "to_dict"):
            return obj.to_dict()

        # Let the base class handle anything else
        return super().default(obj)
