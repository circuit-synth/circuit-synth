#!/usr/bin/env python3
"""
TAC Helper Agent Manager

Manages the lifecycle of helper agents during stage execution:
- Spawns helper agents from templates
- Tracks helper agent execution in database
- Collects results and aggregates costs
- Provides async context manager for clean lifecycle management

Usage Example:
--------------
```python
from adw_modules.tac_helper_manager import HelperAgentManager
from adw_modules.tac_database import TACDatabase

db = TACDatabase()
await db.connect()

manager = HelperAgentManager(db)

# Spawn a helper agent
async with manager.spawn_helper(
    task_id=task_id,
    stage_id=stage_id,
    template_name="research-agent",
    purpose="Find relevant test files"
) as helper:
    # Helper is now running
    print(f"Helper ID: {helper.helper_id}")
    print(f"Agent name: {helper.agent_name}")

    # Simulate work (in real use, helper would execute)
    result = await helper.run(prompt="Search for test files")

    # Helper automatically completes when exiting context
    # Cost is automatically rolled up to parent task
```
"""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, AsyncIterator
from uuid import UUID
from decimal import Decimal
from contextlib import asynccontextmanager
from dataclasses import dataclass

from .tac_database import TACDatabase
from .tac_models import HelperAgentCreate, HelperAgentModel
from .tac_agent_loader import AgentTemplateLoader

logger = logging.getLogger(__name__)


@dataclass
class HelperContext:
    """
    Context object for a spawned helper agent.

    Provides access to helper metadata and execution control.
    """
    helper_id: UUID
    task_id: UUID
    stage_id: Optional[UUID]
    agent_name: str
    agent_template: str
    template_config: Dict[str, Any]
    database: TACDatabase

    # Overrides
    provider_override: Optional[str] = None
    model_override: Optional[str] = None

    # Execution tracking
    input_tokens: int = 0
    output_tokens: int = 0
    cost: Decimal = Decimal("0")
    result_summary: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    async def log_event(
        self,
        event_type: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Log an event for this helper agent"""
        from .tac_models import EventCreate

        await self.database.log_event(
            EventCreate(
                task_id=self.task_id,
                stage_id=self.stage_id,
                helper_agent_id=self.helper_id,
                event_category="helper",
                event_type=event_type,
                content=content,
                summary=summary,
                payload=payload,
            )
        )

    async def update_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal,
    ):
        """Update token usage and cost for this helper"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost += cost

        await self.log_event(
            event_type="TokenUsage",
            summary=f"Used {input_tokens} input, {output_tokens} output tokens",
            payload={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": str(cost),
                "total_cost": str(self.cost),
            },
        )

    async def set_result(
        self,
        summary: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Set the result summary and data for this helper"""
        self.result_summary = summary
        self.result_data = data or {}

        await self.log_event(
            event_type="ResultReady",
            summary=summary,
            payload=data,
        )

    async def run(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the helper agent with a prompt using real LLM API.

        Args:
            prompt: The task prompt for the helper agent
            **kwargs: Additional arguments for agent execution

        Returns:
            Dictionary containing agent result with:
            - status: "success" or "error"
            - content: LLM response content
            - provider: LLM provider used
            - model: Model identifier
            - error: Error message (if status is "error")
        """
        await self.log_event(
            event_type="ExecutionStarted",
            summary="Helper agent execution started",
            content=prompt,
        )

        try:
            # Import LLM client
            from .llm_client import LLMClient, LLMResponse

            # Extract configuration from template with overrides
            # Priority: kwargs > context overrides > template config > defaults
            provider = (
                kwargs.get("provider") or
                self.provider_override or
                self.template_config.get("provider", "anthropic")
            )
            model = (
                kwargs.get("model") or
                self.model_override or
                self.template_config.get("model")
            )
            temperature = float(kwargs.get("temperature", self.template_config.get("temperature", 0.7)))
            max_tokens = int(kwargs.get("max_tokens", self.template_config.get("max_tokens", 4096)))

            # Get system prompt from template config
            system_prompt = self.template_config.get("system_prompt", "")

            # Create LLM client
            client = LLMClient(
                provider=provider,
                model=model or "claude-3-5-haiku-20241022",  # Default model
                temperature=temperature,
                max_tokens=max_tokens,
            )

            logger.info(
                f"Executing helper {self.agent_name} with {provider}/{client.model}"
            )

            # Execute LLM call
            response: LLMResponse = await client.call(
                system_prompt=system_prompt,
                user_message=prompt,
            )

            # Update usage tracking with real tokens and cost
            await self.update_usage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=response.cost,
            )

            logger.info(
                f"Helper {self.agent_name} completed: "
                f"{response.input_tokens} → {response.output_tokens} tokens, "
                f"${response.cost}"
            )

            result = {
                "status": "success",
                "content": response.content,
                "provider": response.provider,
                "model": response.model,
            }

            await self.set_result(
                summary=f"Helper execution completed successfully ({response.model})",
                data=result,
            )

            return result

        except Exception as e:
            logger.error(f"Helper {self.agent_name} execution failed: {e}")

            await self.log_event(
                event_type="ExecutionError",
                summary=f"Helper execution failed: {str(e)}",
                content=str(e),
            )

            result = {
                "status": "error",
                "error": str(e),
                "prompt": prompt,
            }

            await self.set_result(
                summary=f"Helper execution failed: {str(e)}",
                data=result,
            )

            return result


class HelperAgentManager:
    """
    Manages helper agent lifecycle for TAC architecture.

    Responsibilities:
    - Load agent templates from database
    - Spawn helper agents with unique names
    - Track helper execution in database
    - Collect results and aggregate costs to parent task
    """

    def __init__(self, database: TACDatabase):
        """
        Initialize helper agent manager.

        Args:
            database: Connected TACDatabase instance
        """
        self.db = database
        self.template_loader = AgentTemplateLoader()
        logger.info("HelperAgentManager initialized")

    def _generate_agent_name(self, template_name: str) -> str:
        """
        Generate a unique agent name.

        Format: {template_name}-{short_uuid}
        Example: research-agent-a1b2c3

        Args:
            template_name: Base template name

        Returns:
            Unique agent name
        """
        short_uuid = str(uuid.uuid4())[:6]
        return f"{template_name}-{short_uuid}"

    async def get_template_config(
        self,
        template_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent template configuration from database.

        Args:
            template_name: Name of the template

        Returns:
            Template configuration dict, or None if not found
        """
        template = await self.db.get_agent_template(template_name)

        if template is None:
            logger.warning(f"Template not found: {template_name}")
            return None

        return {
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "model": template.model,
            "temperature": template.temperature,
            "tools": template.tools,
            "color": template.color,
        }

    @asynccontextmanager
    async def spawn_helper(
        self,
        task_id: UUID,
        template_name: str,
        purpose: str,
        stage_id: Optional[UUID] = None,
        provider: Optional[str] = None,
        model_override: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[HelperContext]:
        """
        Spawn a helper agent and manage its lifecycle.

        Context manager that:
        1. Loads template from database
        2. Creates helper record in database
        3. Yields HelperContext for execution
        4. Automatically completes helper and aggregates cost on exit

        Args:
            task_id: Parent task UUID
            template_name: Name of agent template to use
            purpose: Human-readable purpose of this helper
            stage_id: Optional parent stage UUID
            provider: Optional provider override (e.g., "openrouter")
            model_override: Optional model override (overrides template default)
            metadata: Optional metadata dict

        Yields:
            HelperContext for agent execution

        Example:
            async with manager.spawn_helper(
                task_id=task_id,
                stage_id=stage_id,
                template_name="research-agent",
                purpose="Find test files"
            ) as helper:
                result = await helper.run("Search for test files")
        """
        # Load template configuration
        template_config = await self.get_template_config(template_name)

        if template_config is None:
            raise ValueError(f"Agent template not found: {template_name}")

        # Generate unique agent name
        agent_name = self._generate_agent_name(template_name)

        # Determine model to use
        model = model_override or template_config["model"]

        # Merge metadata
        full_metadata = {
            "purpose": purpose,
            "template_description": template_config["description"],
            **(metadata or {}),
        }

        # Create helper record in database
        helper_create = HelperAgentCreate(
            task_id=task_id,
            stage_id=stage_id,
            agent_name=agent_name,
            agent_template=template_name,
            provider=provider,
            model=model,
            metadata=full_metadata,
        )

        helper_id = await self.db.create_helper(helper_create)

        logger.info(
            f"Spawned helper: {agent_name} "
            f"(template={template_name}, helper_id={helper_id})"
        )

        # Create context
        context = HelperContext(
            helper_id=helper_id,
            task_id=task_id,
            stage_id=stage_id,
            agent_name=agent_name,
            agent_template=template_name,
            template_config=template_config,
            database=self.db,
            provider_override=provider,
            model_override=model_override,
        )

        # Log spawn event
        await context.log_event(
            event_type="HelperSpawned",
            summary=f"Spawned {agent_name}",
            content=purpose,
            payload={
                "template": template_name,
                "model": model,
                "provider": provider,
            },
        )

        try:
            # Yield context for use
            yield context

            # On successful completion
            logger.info(
                f"Helper {agent_name} completed successfully "
                f"(cost: ${context.cost})"
            )

            # Update helper completion in database
            await self.db.update_helper_completion(
                helper_id=helper_id,
                status="completed",
                input_tokens=context.input_tokens,
                output_tokens=context.output_tokens,
                cost=context.cost,
                result_summary=context.result_summary,
                result_data=context.result_data,
            )

            await context.log_event(
                event_type="HelperCompleted",
                summary=f"Completed: {context.result_summary or 'No summary'}",
                payload={
                    "input_tokens": context.input_tokens,
                    "output_tokens": context.output_tokens,
                    "cost": str(context.cost),
                },
            )

        except Exception as e:
            # On error
            error_msg = str(e)
            logger.error(
                f"Helper {agent_name} errored: {error_msg}",
                exc_info=True
            )

            # Update helper as errored
            await self.db.update_helper_completion(
                helper_id=helper_id,
                status="errored",
                input_tokens=context.input_tokens,
                output_tokens=context.output_tokens,
                cost=context.cost,
                result_summary=f"Error: {error_msg}",
                result_data={"error": error_msg},
            )

            await context.log_event(
                event_type="HelperErrored",
                summary=f"Error: {error_msg}",
                content=str(e),
            )

            # Re-raise exception
            raise

    async def list_active_helpers(
        self,
        task_id: Optional[UUID] = None,
        stage_id: Optional[UUID] = None,
    ) -> list[HelperAgentModel]:
        """
        List active helper agents.

        Args:
            task_id: Optional filter by task
            stage_id: Optional filter by stage

        Returns:
            List of active helper agents
        """
        # TODO: Add database query for active helpers
        # For now, return empty list
        logger.warning("list_active_helpers not yet fully implemented")
        return []
