#!/usr/bin/env python3
"""
LLM Provider Abstraction Layer

Provides unified interface for multiple LLM providers (Anthropic, OpenAI, etc.)
enabling swappable agents in TAC-X pipeline.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # {"input_tokens": X, "output_tokens": Y}
    raw_response: Any  # Original provider response
    success: bool
    error: Optional[str] = None


class LLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def invoke(self, prompt: str, system_prompt: Optional[str] = None,
               temperature: float = 1.0, max_tokens: Optional[int] = None) -> LLMResponse:
        """
        Invoke the LLM with given prompt.

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with standardized fields
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses"""
        pass

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD for given token usage.
        Override in subclasses with provider-specific pricing.
        """
        return 0.0


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    # Pricing per million tokens (as of 2025-01)
    PRICING = {
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-haiku-4-5": {"input": 0.8, "output": 4.0},
    }

    def __init__(self, model: str, api_key: Optional[str] = None):
        super().__init__(model, api_key or os.getenv("ANTHROPIC_API_KEY"))

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Import anthropic SDK
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def invoke(self, prompt: str, system_prompt: Optional[str] = None,
               temperature: float = 1.0, max_tokens: Optional[int] = None) -> LLMResponse:
        """Invoke Claude API"""

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Build request params
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 8192,
            }

            if system_prompt:
                params["system"] = system_prompt

            logger.debug(f"Invoking Anthropic {self.model} with {len(prompt)} chars")

            # Call API
            response = self.client.messages.create(**params)

            # Extract content
            content = response.content[0].text if response.content else ""

            # Extract usage
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

            logger.info(f"Anthropic response: {usage['input_tokens']} in / {usage['output_tokens']} out")

            return LLMResponse(
                content=content,
                model=self.model,
                provider="anthropic",
                usage=usage,
                raw_response=response,
                success=True
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                provider="anthropic",
                usage={"input_tokens": 0, "output_tokens": 0},
                raw_response=None,
                success=False,
                error=str(e)
            )

    def supports_streaming(self) -> bool:
        return True

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on Anthropic pricing"""
        pricing = self.PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 4)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""

    # Pricing per million tokens (as of 2025-01)
    PRICING = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    }

    def __init__(self, model: str, api_key: Optional[str] = None):
        super().__init__(model, api_key or os.getenv("OPENAI_API_KEY"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Import openai SDK
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def invoke(self, prompt: str, system_prompt: Optional[str] = None,
               temperature: float = 1.0, max_tokens: Optional[int] = None) -> LLMResponse:
        """Invoke OpenAI API"""

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Build request params
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            logger.debug(f"Invoking OpenAI {self.model} with {len(prompt)} chars")

            # Call API
            response = self.client.chat.completions.create(**params)

            # Extract content
            content = response.choices[0].message.content or ""

            # Extract usage
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

            logger.info(f"OpenAI response: {usage['input_tokens']} in / {usage['output_tokens']} out")

            return LLMResponse(
                content=content,
                model=self.model,
                provider="openai",
                usage=usage,
                raw_response=response,
                success=True
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                provider="openai",
                usage={"input_tokens": 0, "output_tokens": 0},
                raw_response=None,
                success=False,
                error=str(e)
            )

    def supports_streaming(self) -> bool:
        return True

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on OpenAI pricing"""
        pricing = self.PRICING.get(self.model, {"input": 10.0, "output": 30.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 4)


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider - unified API gateway for multiple LLMs"""

    # OpenRouter uses per-model pricing, these are approximations
    PRICING = {
        "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "anthropic/claude-opus-4": {"input": 15.0, "output": 75.0},
        "anthropic/claude-haiku-4": {"input": 0.8, "output": 4.0},
        "openai/gpt-4": {"input": 30.0, "output": 60.0},
        "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "openai/gpt-4o": {"input": 2.5, "output": 10.0},
    }

    def __init__(self, model: str, api_key: Optional[str] = None):
        super().__init__(model, api_key or os.getenv("OPENROUTER_API_KEY"))

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        # Import openai SDK (OpenRouter is compatible with OpenAI API)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def invoke(self, prompt: str, system_prompt: Optional[str] = None,
               temperature: float = 1.0, max_tokens: Optional[int] = None) -> LLMResponse:
        """Invoke OpenRouter API"""

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Build request params
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            logger.debug(f"Invoking OpenRouter {self.model} with {len(prompt)} chars")

            # Call API
            response = self.client.chat.completions.create(**params)

            # Extract content
            content = response.choices[0].message.content or ""

            # Extract usage
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

            logger.info(f"OpenRouter response: {usage['input_tokens']} in / {usage['output_tokens']} out")

            return LLMResponse(
                content=content,
                model=self.model,
                provider="openrouter",
                usage=usage,
                raw_response=response,
                success=True
            )

        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                provider="openrouter",
                usage={"input_tokens": 0, "output_tokens": 0},
                raw_response=None,
                success=False,
                error=str(e)
            )

    def supports_streaming(self) -> bool:
        return True

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on OpenRouter pricing"""
        # Try to find specific model pricing
        pricing = self.PRICING.get(self.model, {"input": 5.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 4)


class ProviderRegistry:
    """Registry for LLM providers with factory methods"""

    _providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
    }

    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a new provider"""
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def create(cls, provider: str, model: str, api_key: Optional[str] = None) -> LLMProvider:
        """
        Create provider instance.

        Args:
            provider: Provider name (anthropic, openai, etc.)
            model: Model identifier
            api_key: Optional API key (defaults to env var)

        Returns:
            LLMProvider instance
        """
        provider_lower = provider.lower()

        if provider_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider: {provider}. Available: {available}")

        provider_class = cls._providers[provider_lower]
        return provider_class(model=model, api_key=api_key)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers"""
        return list(cls._providers.keys())


def parse_model_string(model_string: str) -> tuple[str, str]:
    """
    Parse model string in format 'provider/model' or just 'model'.

    Examples:
        "anthropic/claude-sonnet-4-5" -> ("anthropic", "claude-sonnet-4-5")
        "claude-sonnet-4-5" -> ("anthropic", "claude-sonnet-4-5")
        "openai/gpt-4" -> ("openai", "gpt-4")
        "gpt-4" -> ("openai", "gpt-4")
        "openrouter/anthropic/claude-sonnet-4" -> ("openrouter", "anthropic/claude-sonnet-4")

    Returns:
        (provider, model) tuple
    """
    # Special case for openrouter which has nested paths
    if model_string.startswith("openrouter/"):
        return "openrouter", model_string.replace("openrouter/", "", 1)

    if "/" in model_string:
        provider, model = model_string.split("/", 1)
        return provider, model

    # Infer provider from model name
    model_lower = model_string.lower()

    if "claude" in model_lower:
        return "anthropic", model_string
    elif "gpt" in model_lower:
        return "openai", model_string
    else:
        raise ValueError(f"Cannot infer provider from model: {model_string}")


if __name__ == "__main__":
    # Simple test
    print("LLM Provider Abstraction Layer")
    print(f"Available providers: {ProviderRegistry.list_providers()}")

    # Test parsing
    test_models = [
        "anthropic/claude-sonnet-4-5",
        "claude-haiku-4-5",
        "openai/gpt-4",
        "gpt-4o-mini",
    ]

    for model_str in test_models:
        provider, model = parse_model_string(model_str)
        print(f"  {model_str:40} -> provider={provider:10} model={model}")
