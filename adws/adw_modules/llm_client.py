#!/usr/bin/env python3
"""
LLM Client for TAC Helper Agents

Provides unified interface for calling LLM APIs:
- Anthropic (Claude)
- OpenRouter (multi-model gateway)

Features:
- Token counting
- Cost calculation
- Error handling
- Retry logic
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API"""
    content: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    model: str
    provider: str


class LLMClient:
    """
    Unified LLM client for TAC helper agents.

    Supports:
    - Anthropic Claude API
    - OpenRouter (multi-model gateway)
    """

    # Cost per 1M tokens (input, output) for common models
    COSTS = {
        "claude-3-5-sonnet-20241022": (Decimal("3.00"), Decimal("15.00")),
        "claude-3-5-haiku-20241022": (Decimal("0.80"), Decimal("4.00")),
        "claude-3-haiku-20240307": (Decimal("0.25"), Decimal("1.25")),
        "anthropic/claude-3-5-sonnet": (Decimal("3.00"), Decimal("15.00")),
        "anthropic/claude-3-5-haiku": (Decimal("0.80"), Decimal("4.00")),
        "anthropic/claude-3-haiku": (Decimal("0.25"), Decimal("1.25")),
    }

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-3-5-haiku-20241022",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize LLM client.

        Args:
            provider: "anthropic" or "openrouter"
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize API client based on provider
        if self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "openrouter":
            self._init_openrouter()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Initialized Anthropic client with model: {self.model}")

    def _init_openrouter(self):
        """Initialize OpenRouter client (uses httpx for HTTP calls)"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        logger.info(f"Initialized OpenRouter client with model: {self.model}")

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """Calculate cost based on token usage"""
        # Get cost per 1M tokens
        if model in self.COSTS:
            input_cost_per_m, output_cost_per_m = self.COSTS[model]
        else:
            # Default to Haiku pricing if model not found
            logger.warning(f"Cost not found for model {model}, using Haiku pricing")
            input_cost_per_m, output_cost_per_m = self.COSTS["claude-3-haiku-20240307"]

        # Calculate cost
        input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * input_cost_per_m
        output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * output_cost_per_m

        return input_cost + output_cost

    async def call(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> LLMResponse:
        """
        Call LLM API with retry logic.

        Args:
            system_prompt: System prompt for the model
            user_message: User message/task
            **kwargs: Additional API parameters

        Returns:
            LLMResponse with content, tokens, and cost
        """
        if self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, user_message, **kwargs)
        elif self.provider == "openrouter":
            return await self._call_openrouter(system_prompt, user_message, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> LLMResponse:
        """Call Anthropic API"""
        logger.debug(f"Calling Anthropic API: model={self.model}")

        try:
            # Make API call (Anthropic SDK is sync, run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ],
                    **kwargs
                )
            )

            # Extract response
            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate cost
            cost = self._calculate_cost(self.model, input_tokens, output_tokens)

            logger.info(
                f"Anthropic API call successful: "
                f"{input_tokens} → {output_tokens} tokens, ${cost}"
            )

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model=self.model,
                provider="anthropic"
            )

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def _call_openrouter(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> LLMResponse:
        """Call OpenRouter API"""
        import httpx

        logger.debug(f"Calling OpenRouter API: model={self.model}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        **kwargs
                    }
                )

                response.raise_for_status()
                data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]
            input_tokens = data["usage"]["prompt_tokens"]
            output_tokens = data["usage"]["completion_tokens"]

            # Calculate cost
            cost = self._calculate_cost(self.model, input_tokens, output_tokens)

            logger.info(
                f"OpenRouter API call successful: "
                f"{input_tokens} → {output_tokens} tokens, ${cost}"
            )

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model=self.model,
                provider="openrouter"
            )

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise
