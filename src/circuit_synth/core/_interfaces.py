"""Minimal interfaces for the open source circuit-synth package."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


# Base interfaces for circuit models
class ICircuitModel(ABC):
    """Interface for circuit models."""

    pass


class IComponentModel(ABC):
    """Interface for component models."""

    pass


class IPinModel(ABC):
    """Interface for pin models."""

    pass


class INetModel(ABC):
    """Interface for net models."""

    pass


# Factory interfaces
class CircuitModelFactory(ABC):
    """Factory for creating circuit models."""

    pass


class ComponentModelFactory(ABC):
    """Factory for creating component models."""

    pass


class NetModelFactory(ABC):
    """Factory for creating net models."""

    pass


class PinModelFactory(ABC):
    """Factory for creating pin models."""

    pass


# KiCad integration interfaces
class IKiCadIntegration(ABC):
    """Interface for KiCad integration."""

    pass


class ISchematicGenerator(ABC):
    """Interface for schematic generation."""

    pass


class IPCBGenerator(ABC):
    """Interface for PCB generation."""

    pass


class ISymbolLibrary(ABC):
    """Interface for symbol libraries."""

    pass


class IFootprintLibrary(ABC):
    """Interface for footprint libraries."""

    pass


# Intelligence system interfaces (minimal stubs for open source)
class ILLMProvider(ABC):
    """Interface for LLM providers."""

    pass


class ILLMManager(ABC):
    """Interface for LLM management."""

    pass


class IAgent(ABC):
    """Interface for agents."""

    pass


class IAgentManager(ABC):
    """Interface for agent management."""

    pass


class IKnowledgeBase(ABC):
    """Interface for knowledge base."""

    pass


class IPromptTemplate(ABC):
    """Interface for prompt templates."""

    pass


class IPromptManager(ABC):
    """Interface for prompt management."""

    pass


# Factory classes
class LLMProviderFactory(ABC):
    """Factory for LLM providers."""

    pass


class AgentFactory(ABC):
    """Factory for agents."""

    pass


class KnowledgeBaseFactory(ABC):
    """Factory for knowledge base."""

    pass


class PromptManagerFactory(ABC):
    """Factory for prompt managers."""

    pass
