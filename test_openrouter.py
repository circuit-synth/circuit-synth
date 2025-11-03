#!/usr/bin/env python3
"""
Test OpenRouter provider integration
"""

import os
import sys
from pathlib import Path

# Add adws module to path
sys.path.insert(0, str(Path(__file__).parent / "adws"))

from adw_modules.llm_providers import ProviderRegistry, OpenRouterProvider

def test_openrouter():
    """Test OpenRouter provider"""

    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable not set")
        print("   Please set it to test OpenRouter integration")
        return False

    print("🧪 Testing OpenRouter Provider")
    print("=" * 60)

    # Test 1: Create provider
    print("\n1. Creating OpenRouter provider...")
    try:
        provider = ProviderRegistry.create(
            provider="openrouter",
            model="anthropic/claude-3.5-sonnet"
        )
        print(f"   ✓ Provider created: {provider.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ Failed to create provider: {e}")
        return False

    # Test 2: Simple invocation
    print("\n2. Testing simple invocation...")
    try:
        response = provider.invoke(
            prompt="Say 'Hello from OpenRouter!' and nothing else.",
            temperature=0.5,
            max_tokens=100
        )

        if response.success:
            print(f"   ✓ Response received")
            print(f"   Content: {response.content[:100]}")
            print(f"   Tokens: {response.usage['input_tokens']} in / {response.usage['output_tokens']} out")
            print(f"   Cost: ${provider.get_cost_estimate(response.usage['input_tokens'], response.usage['output_tokens'])}")
        else:
            print(f"   ❌ Response failed: {response.error}")
            return False

    except Exception as e:
        print(f"   ❌ Invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Different model
    print("\n3. Testing different model (Claude Haiku via OpenRouter)...")
    try:
        provider2 = ProviderRegistry.create(
            provider="openrouter",
            model="anthropic/claude-3-haiku"
        )

        response2 = provider2.invoke(
            prompt="What is 2+2? Answer with just the number.",
            temperature=0.0,
            max_tokens=10
        )

        if response2.success:
            print(f"   ✓ Response: {response2.content.strip()}")
            print(f"   Tokens: {response2.usage['input_tokens']} in / {response2.usage['output_tokens']} out")
        else:
            print(f"   ❌ Failed: {response2.error}")

    except Exception as e:
        print(f"   ⚠️  Second test failed (non-critical): {e}")

    print("\n" + "=" * 60)
    print("✅ OpenRouter integration test complete!")
    return True


def test_workflow_with_openrouter():
    """Test workflow configuration with OpenRouter"""
    from adw_modules.workflow_config import WorkflowConfig, StageConfig

    print("\n🧪 Testing Workflow Configuration with OpenRouter")
    print("=" * 60)

    # Create workflow with OpenRouter
    workflow = WorkflowConfig(
        name="OpenRouter Test Workflow",
        version="1.0.0",
        description="Test workflow using OpenRouter",
        stages=[
            StageConfig(
                name="planning",
                agent="planner",
                provider="openrouter",
                model="anthropic/claude-3.5-sonnet",
                fallback="anthropic/claude-3-opus",
                temperature=1.0
            ),
            StageConfig(
                name="building",
                agent="builder",
                provider="openrouter",
                model="anthropic/claude-3.5-sonnet",
                temperature=1.0
            ),
        ]
    )

    print("\n1. Workflow created:")
    for stage in workflow.stages:
        print(f"   - {stage.name}: {stage.provider}/{stage.model}")
        if stage.fallback:
            print(f"     Fallback: {stage.fallback}")

    # Generate Mermaid diagram
    print("\n2. Workflow diagram:")
    diagram = workflow.to_mermaid()
    for line in diagram.split("\n"):
        print(f"   {line}")

    # Save to YAML
    print("\n3. Saving workflow to YAML...")
    output_path = Path("/tmp/openrouter-workflow.yaml")
    workflow.to_yaml(output_path)
    print(f"   ✓ Saved to {output_path}")

    # Load back
    print("\n4. Loading workflow from YAML...")
    loaded = WorkflowConfig.from_yaml(output_path)
    print(f"   ✓ Loaded: {loaded.name}")
    print(f"   ✓ Stages: {len(loaded.stages)}")

    print("\n" + "=" * 60)
    print("✅ Workflow configuration test complete!")


if __name__ == "__main__":
    print("OpenRouter Integration Test")
    print("=" * 60)

    # Test provider
    if test_openrouter():
        # Test workflow config
        test_workflow_with_openrouter()
    else:
        print("\n❌ Provider test failed, skipping workflow test")
        sys.exit(1)
