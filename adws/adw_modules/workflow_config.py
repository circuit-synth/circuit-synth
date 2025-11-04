#!/usr/bin/env python3
"""
TAC-X Workflow Configuration

Defines and parses workflow YAML configurations for swappable agents.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StageConfig:
    """Configuration for a single pipeline stage"""
    name: str
    agent: str  # Agent prompt file (e.g., "planner", "builder")
    provider: str  # LLM provider (anthropic, openai, etc.)
    model: str  # Model identifier
    fallback: Optional[str] = None  # Fallback model string (provider/model)
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    tools: List[str] = field(default_factory=list)

    def get_model_string(self) -> str:
        """Get full model string (provider/model)"""
        return f"{self.provider}/{self.model}"

    def get_fallback_parts(self) -> Optional[tuple[str, str]]:
        """Parse fallback into (provider, model) tuple"""
        if not self.fallback:
            return None

        if "/" in self.fallback:
            provider, model = self.fallback.split("/", 1)
            return provider, model

        # Infer provider
        if "claude" in self.fallback.lower():
            return "anthropic", self.fallback
        elif "gpt" in self.fallback.lower():
            return "openai", self.fallback
        else:
            return None


@dataclass
class WorkflowConfig:
    """Complete workflow configuration"""
    name: str
    version: str
    description: str
    stages: List[StageConfig]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "WorkflowConfig":
        """Load workflow from YAML file"""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        workflow_data = data.get("workflow", {})

        stages = []
        for stage_data in workflow_data.get("stages", []):
            stage = StageConfig(
                name=stage_data["name"],
                agent=stage_data["agent"],
                provider=stage_data["provider"],
                model=stage_data["model"],
                fallback=stage_data.get("fallback"),
                temperature=stage_data.get("temperature", 1.0),
                max_tokens=stage_data.get("max_tokens"),
                tools=stage_data.get("tools", [])
            )
            stages.append(stage)

        return cls(
            name=workflow_data.get("name", "TAC-X Pipeline"),
            version=workflow_data.get("version", "1.0.0"),
            description=workflow_data.get("description", ""),
            stages=stages,
            metadata=workflow_data.get("metadata", {})
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "WorkflowConfig":
        """Create workflow from dict (for programmatic config)"""
        stages = []
        for stage_data in config_dict.get("stages", []):
            stage = StageConfig(**stage_data)
            stages.append(stage)

        return cls(
            name=config_dict.get("name", "TAC-X Pipeline"),
            version=config_dict.get("version", "1.0.0"),
            description=config_dict.get("description", ""),
            stages=stages,
            metadata=config_dict.get("metadata", {})
        )

    def to_yaml(self, output_path: Path):
        """Save workflow to YAML file"""
        data = {
            "workflow": {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "stages": [
                    {
                        "name": stage.name,
                        "agent": stage.agent,
                        "provider": stage.provider,
                        "model": stage.model,
                        "fallback": stage.fallback,
                        "temperature": stage.temperature,
                        "max_tokens": stage.max_tokens,
                        "tools": stage.tools,
                    }
                    for stage in self.stages
                ],
                "metadata": self.metadata,
            }
        }

        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved workflow config to {output_path}")

    def get_stage(self, stage_name: str) -> Optional[StageConfig]:
        """Get stage config by name"""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None

    def to_mermaid(self) -> str:
        """
        Generate Mermaid diagram of workflow.

        Returns:
            Mermaid diagram as string
        """
        lines = ["graph LR"]
        lines.append(f"    Start([Start]) --> Stage1")

        for i, stage in enumerate(self.stages, 1):
            stage_id = f"Stage{i}"
            next_id = f"Stage{i+1}" if i < len(self.stages) else "End"

            # Stage node with provider/model info
            label = f"{stage.name}\\n{stage.provider}/{stage.model}"
            lines.append(f"    {stage_id}[\"{label}\"]")

            # Add fallback if exists
            if stage.fallback:
                lines.append(f"    {stage_id} -.fallback.-> Fallback{i}[\"{stage.fallback}\"]")

            # Connect to next stage
            if i < len(self.stages):
                lines.append(f"    {stage_id} --> {next_id}")
            else:
                lines.append(f"    {stage_id} --> End([End])")

        return "\n".join(lines)


def create_default_workflow() -> WorkflowConfig:
    """Create default TAC-X workflow configuration"""
    return WorkflowConfig(
        name="TAC-X Default Pipeline",
        version="1.0.0",
        description="Default multi-stage autonomous development pipeline",
        stages=[
            StageConfig(
                name="planning",
                agent="planner",
                provider="anthropic",
                model="claude-sonnet-4-5",
                fallback="anthropic/claude-opus-4",
                temperature=1.0,
                tools=["Read", "Grep", "Glob", "Bash"]
            ),
            StageConfig(
                name="building",
                agent="builder",
                provider="anthropic",
                model="claude-sonnet-4-5",
                fallback="anthropic/claude-opus-4",
                temperature=1.0,
                tools=["Read", "Edit", "Write", "Bash", "Grep", "Glob"]
            ),
            StageConfig(
                name="reviewing",
                agent="reviewer",
                provider="anthropic",
                model="claude-sonnet-4-5",
                fallback="openai/gpt-4-turbo",
                temperature=1.0,
                tools=["Read", "Bash", "Grep", "Glob"]
            ),
            StageConfig(
                name="pr_creation",
                agent="pr-creator",
                provider="anthropic",
                model="claude-haiku-4-5",
                fallback="openai/gpt-4o-mini",
                temperature=1.0,
                tools=["Read", "Bash"]
            ),
        ],
        metadata={
            "created_by": "TAC-X System",
            "optimization": "cost-effective",
            "notes": "Uses Haiku for simple PR creation, Sonnet for complex work"
        }
    )


def validate_workflow(config: WorkflowConfig) -> List[str]:
    """
    Validate workflow configuration.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not config.name:
        errors.append("Workflow must have a name")

    if not config.stages:
        errors.append("Workflow must have at least one stage")

    # Check stage names are unique
    stage_names = [s.name for s in config.stages]
    if len(stage_names) != len(set(stage_names)):
        errors.append("Stage names must be unique")

    # Validate each stage
    for i, stage in enumerate(config.stages):
        prefix = f"Stage {i+1} ({stage.name})"

        if not stage.agent:
            errors.append(f"{prefix}: agent is required")

        if not stage.provider:
            errors.append(f"{prefix}: provider is required")

        if not stage.model:
            errors.append(f"{prefix}: model is required")

        if stage.temperature < 0 or stage.temperature > 2:
            errors.append(f"{prefix}: temperature must be 0-2")

        if stage.max_tokens and stage.max_tokens < 1:
            errors.append(f"{prefix}: max_tokens must be positive")

    return errors


if __name__ == "__main__":
    # Generate default workflow
    print("Creating default TAC-X workflow...")

    workflow = create_default_workflow()

    # Save to YAML
    output_path = Path("workflow.yaml")
    workflow.to_yaml(output_path)
    print(f"Saved to {output_path}")

    # Generate Mermaid diagram
    print("\nMermaid Diagram:")
    print(workflow.to_mermaid())

    # Validate
    errors = validate_workflow(workflow)
    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ Workflow is valid")
