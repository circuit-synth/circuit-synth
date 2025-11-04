# TAC-X Multi-Provider Integration - Comprehensive Implementation Plan

**Date**: 2025-11-03
**Author**: Claude Code (Sonnet 4.5)
**Status**: Research Complete - Implementation Plan
**Related**: Issue #506, PR #507

---

## Executive Summary

Based on deep research into LLM provider tool calling APIs and analysis of the current TAC-X architecture, this plan outlines how to achieve full multi-provider support with tool calling across Anthropic Claude, OpenAI GPT, Google Gemini, X-AI Grok, and any OpenRouter-supported model.

**Key Finding**: OpenRouter ALREADY handles tool call format transformation between providers, significantly simplifying our implementation.

---

## Table of Contents

1. [Problem Analysis](#problem-analysis)
2. [Research Findings](#research-findings)
3. [Architecture Design](#architecture-design)
4. [Implementation Phases](#implementation-phases)
5. [Testing Strategy](#testing-strategy)
6. [Cost Optimization Strategies](#cost-optimization-strategies)
7. [Risk Analysis & Mitigation](#risk-analysis--mitigation)
8. [Success Criteria](#success-criteria)

---

## Problem Analysis

### Current State

**✅ What Works:**
- Provider abstraction layer (`llm_providers.py`)
- Workflow configuration system (`workflow_config.py`)
- OpenRouter integration for simple text responses
- Token tracking and cost estimation
- Multi-stage pipeline architecture

**❌ What Doesn't Work:**
- Tool calling / function calling integration
- Response format parsing from non-Claude models
- Tool execution from LLM responses
- Mixed-model workflows (different models per stage)
- Fallback mechanism validation

### Root Cause Analysis

**Issue #1: Tool Calling Not Integrated**

The current `LLMProvider` classes don't support tool calling:
```python
def invoke(self, prompt: str, system_prompt: Optional[str] = None,
           temperature: float = 1.0, max_tokens: Optional[int] = None) -> LLMResponse:
```

Notice: No `tools` parameter!

**Issue #2: Response Format Mismatch**

TAC-X pipeline expects Claude-specific format, but receives different formats:

- **Claude**: Structured tool use JSON
- **OpenAI**: Function calling JSON
- **Gemini**: Mixed format (markdown + JSON)
- **Grok**: Unknown (likely OpenAI-compatible)

**Issue #3: No Tool Execution Layer**

When LLM requests a tool (bash command, file read, etc.), there's no:
1. Parser to extract tool requests from response
2. Executor to run the tool
3. Feedback loop to send results back to LLM

---

## Research Findings

### Key Discovery: OpenRouter Handles Format Transformation!

**From OpenRouter Documentation:**

> "OpenRouter standardizes the tool calling interface across models and providers. Tool calling parameter follows OpenAI's tool calling request shape. **For non-OpenAI providers, it will be transformed accordingly.**"

**Impact**: We only need to implement ONE tool calling format (OpenAI-compatible), and OpenRouter handles transformation!

### Tool Calling Formats Across Providers

#### 1. **OpenAI Format** (Standard for OpenRouter)

**Request:**
```json
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "execute_bash",
      "description": "Execute a bash command",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {"type": "string", "description": "Bash command to execute"}
        },
        "required": ["command"]
      }
    }
  }]
}
```

**Response:**
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "execute_bash",
          "arguments": "{\"command\": \"ls -la\"}"
        }
      }]
    }
  }]
}
```

#### 2. **Anthropic Format** (Native Claude API)

**Request:**
```json
{
  "tools": [{
    "name": "execute_bash",
    "description": "Execute a bash command",
    "input_schema": {
      "type": "object",
      "properties": {
        "command": {"type": "string", "description": "Bash command"}
      },
      "required": ["command"]
    }
  }]
}
```

**Response:**
```json
{
  "content": [{
    "type": "tool_use",
    "id": "toolu_abc123",
    "name": "execute_bash",
    "input": {"command": "ls -la"}
  }]
}
```

#### 3. **Google Gemini Format** (Native Gemini API)

**Request:**
```json
{
  "tools": [{
    "function_declarations": [{
      "name": "execute_bash",
      "description": "Execute a bash command",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {"type": "string"}
        }
      }
    }]
  }]
}
```

**Response:**
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "function_call": {
          "name": "execute_bash",
          "args": {"command": "ls -la"}
        }
      }]
    }
  }]
}
```

### Solution Libraries Research

#### **Option A: Use OpenRouter's Built-in Transformation**
- ✅ No additional code needed
- ✅ Supports all OpenRouter models
- ✅ Maintained by OpenRouter team
- ⚠️ Only works via OpenRouter (not direct APIs)
- ⚠️ Limited to models OpenRouter supports

#### **Option B: Implement Unified Adapter (Like LangChain)**
- ✅ Works with direct APIs and OpenRouter
- ✅ Full control over behavior
- ✅ Can add custom tools
- ❌ More code to maintain
- ❌ Need to keep up with provider API changes

#### **Option C: Use Existing Library**

**Libraries Found:**
1. **LangChain** - Heavy dependency, overkill for our needs
2. **llm-bridge** (TypeScript) - Not Python
3. **uni-api** - Full proxy server, too complex
4. **Unified-AI-Router** - Similar to what we built

**Recommendation**: Hybrid approach - Use OpenRouter transformation when available, implement adapter for direct APIs.

---

## Architecture Design

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TAC-X Pipeline                              │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Planning │───│ Building │───│ Reviewing│───│ PR Create│     │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘     │
│       │              │              │              │             │
└───────┼──────────────┼──────────────┼──────────────┼─────────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                       │
              ┌────────▼──────────┐
              │  MultiStageWorker │
              └────────┬──────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼────────┐
│ Tool Manager   │           │ Provider        │
│                │           │ Abstraction     │
│ - Define tools │           │                 │
│ - Execute tools│◄──────────┤ - Anthropic     │
│ - Parse results│           │ - OpenAI        │
│ - Feed back    │           │ - OpenRouter    │
└────────────────┘           └─────────────────┘
        │
        ├── Bash Tool
        ├── Read Tool
        ├── Write Tool
        ├── Grep Tool
        └── ... (Claude Code tools)
```

### Component Design

#### **1. Tool Manager** (NEW)

**File**: `adws/adw_modules/tool_manager.py`

**Responsibilities**:
- Define available tools (bash, read, write, grep, etc.)
- Convert tool definitions to provider-specific format
- Parse tool call responses from different providers
- Execute tools and capture output
- Create tool result messages for next LLM turn

**Key Methods**:
```python
class ToolManager:
    def get_tool_definitions(self, provider: str) -> List[Dict]:
        """Get tool definitions in provider-specific format"""

    def parse_tool_calls(self, response: LLMResponse) -> List[ToolCall]:
        """Extract tool calls from LLM response (any provider)"""

    def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool and return result"""

    def create_tool_result_message(self, tool_result: ToolResult) -> Dict:
        """Create message to send tool result back to LLM"""
```

#### **2. Enhanced LLMProvider** (MODIFY)

**Changes to** `adws/adw_modules/llm_providers.py`:

```python
class LLMProvider(ABC):
    @abstractmethod
    def invoke(self,
               prompt: str,
               system_prompt: Optional[str] = None,
               temperature: float = 1.0,
               max_tokens: Optional[int] = None,
               tools: Optional[List[Dict]] = None,  # NEW!
               tool_choice: Optional[str] = None     # NEW!
              ) -> LLMResponse:
        """Invoke LLM with optional tool support"""

    def supports_tools(self) -> bool:
        """Whether this provider supports tool calling"""
        return False  # Override in subclasses
```

**For OpenRouterProvider**:
```python
class OpenRouterProvider(LLMProvider):
    def invoke(self, prompt, system_prompt=None, temperature=1.0,
               max_tokens=None, tools=None, tool_choice=None):
        # Build request with tools (OpenAI format)
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:  # NEW!
            params["tools"] = tools  # OpenRouter transforms automatically!
            if tool_choice:
                params["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**params)

        # Parse response - check for tool calls
        return self._parse_response(response)

    def supports_tools(self) -> bool:
        return True  # OpenRouter supports tools!
```

#### **3. Enhanced MultiStageWorker** (MODIFY)

**Changes to** `adws/adw_modules/multi_stage_worker.py`:

```python
class MultiStageWorker:
    def __init__(self, ...):
        # ... existing code ...
        self.tool_manager = ToolManager()  # NEW!

    def invoke_agent_with_tools(self, stage: str, prompt_file: Path,
                                context_vars: Dict[str, str]) -> Dict[str, Any]:
        """Invoke agent with tool calling support"""

        # Get stage config
        stage_config = self.workflow.get_stage(stage)

        # Create provider
        provider = ProviderRegistry.create(
            provider=stage_config.provider,
            model=stage_config.model
        )

        # Get tool definitions for this provider
        tools = None
        if provider.supports_tools():
            tools = self.tool_manager.get_tool_definitions(stage_config.provider)

        # Initial invocation
        response = provider.invoke(
            prompt=prompt_content,
            system_prompt=system_prompt,
            temperature=stage_config.temperature,
            tools=tools  # NEW!
        )

        # Tool execution loop
        while True:
            tool_calls = self.tool_manager.parse_tool_calls(response)

            if not tool_calls:
                break  # No more tools to execute

            # Execute all tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = self.tool_manager.execute_tool(tool_call)
                tool_results.append(result)

            # Send results back to LLM
            tool_result_messages = [
                self.tool_manager.create_tool_result_message(r)
                for r in tool_results
            ]

            # Continue conversation with tool results
            response = provider.invoke(
                prompt=None,  # No new user prompt
                messages=existing_messages + tool_result_messages,
                tools=tools
            )

        return response
```

---

## Implementation Phases

### Phase 1: Tool Manager Foundation (2-3 hours)

**Goal**: Create tool management infrastructure without provider integration

**Tasks**:
1. Create `tool_manager.py` with tool definitions
2. Define `ToolCall` and `ToolResult` dataclasses
3. Implement tool execution for basic tools (bash, read, write)
4. Write unit tests for tool execution

**Deliverables**:
- `adws/adw_modules/tool_manager.py` ✅
- `tests/test_tool_manager.py` ✅
- Tool definitions for: bash, read, write, grep, glob ✅

**Success Criteria**:
- Can define tools in OpenAI format
- Can execute bash commands via ToolManager
- Can execute file read/write via ToolManager
- All tests passing

---

### Phase 2: OpenRouter Tool Calling (3-4 hours)

**Goal**: Enable tool calling via OpenRouter with automatic format transformation

**Tasks**:
1. Update `OpenRouterProvider.invoke()` to accept `tools` parameter
2. Implement response parsing for tool calls (OpenAI format)
3. Update `LLMResponse` dataclass to include `tool_calls`
4. Test with Google Gemini 2.5 Flash
5. Test with X-AI Grok Code Fast 1

**Deliverables**:
- Enhanced `OpenRouterProvider` ✅
- Updated `LLMResponse` with tool_calls field ✅
- Integration test with tool calling ✅

**Success Criteria**:
- OpenRouter provider can send tools in request
- Can parse tool calls from Gemini response
- Can parse tool calls from Grok response
- Tool calls contain: name, arguments, id

---

### Phase 3: Tool Execution Loop (2-3 hours)

**Goal**: Implement agentic loop - LLM requests tool → execute → send result → LLM continues

**Tasks**:
1. Create `invoke_agent_with_tools()` method in MultiStageWorker
2. Implement tool execution loop (while tool_calls exist)
3. Create tool result message formatting
4. Handle multi-turn conversations with tool results
5. Add logging for tool executions

**Deliverables**:
- Tool execution loop in MultiStageWorker ✅
- Logging for each tool call and result ✅
- Test with simple bash command sequence ✅

**Success Criteria**:
- LLM requests bash command → executes → sees output → continues
- Can handle multiple sequential tool calls
- Tool results properly formatted for next turn
- Full conversation history maintained

---

### Phase 4: Direct API Support (Optional - 4-5 hours)

**Goal**: Support tool calling for direct Anthropic and OpenAI APIs (not just OpenRouter)

**Tasks**:
1. Implement tool format conversion in ToolManager
2. Update `AnthropicProvider` with tool support
3. Update `OpenAIProvider` with tool support
4. Implement provider-specific response parsing
5. Test all three providers (Anthropic, OpenAI, OpenRouter)

**Deliverables**:
- Enhanced `AnthropicProvider` with tools ✅
- Enhanced `OpenAIProvider` with tools ✅
- Format conversion in ToolManager ✅

**Success Criteria**:
- Direct Claude API works with tools (Anthropic format)
- Direct OpenAI API works with tools (OpenAI format)
- OpenRouter still works (OpenAI format)
- All three can execute same tools

---

### Phase 5: Integration & Testing (3-4 hours)

**Goal**: Full pipeline integration with comprehensive testing

**Tasks**:
1. Update all 4 prompt templates to leverage tool calling
2. Test mixed-model workflow (Gemini → Claude → GPT → Gemini)
3. Test fallback mechanism with tool calling
4. Create comprehensive integration test suite
5. Document tool calling in WORKFLOW_CONFIGURATION.md

**Deliverables**:
- Updated prompt templates ✅
- Mixed-model workflow test ✅
- Fallback test ✅
- Updated documentation ✅

**Success Criteria**:
- Planning stage uses tools (bash, grep, etc.)
- Building stage uses tools (write files)
- Reviewing stage uses tools (read files)
- Can switch models mid-pipeline with tools
- Fallback works when primary model fails

---

## Testing Strategy

### Unit Tests

**Tool Manager Tests** (`tests/test_tool_manager.py`):
```python
def test_tool_definition_creation()
def test_bash_tool_execution()
def test_read_tool_execution()
def test_write_tool_execution()
def test_tool_call_parsing_openai_format()
def test_tool_call_parsing_anthropic_format()
def test_tool_call_parsing_gemini_format()
```

**Provider Tests** (`tests/test_llm_providers.py`):
```python
def test_openrouter_tool_calling()
def test_anthropic_tool_calling()
def test_openai_tool_calling()
def test_tool_response_parsing()
```

### Integration Tests

**Single-Model Tool Tests** (`tests/integration/test_single_model_tools.py`):
```python
def test_gemini_with_bash_tools()
def test_grok_with_file_tools()
def test_claude_with_grep_tools()
```

**Mixed-Model Workflow Tests** (`tests/integration/test_mixed_workflows.py`):
```python
def test_gemini_planning_claude_building()
def test_cheap_planning_expensive_building()
def test_multi_provider_pipeline()
```

**Fallback Tests** (`tests/integration/test_fallbacks.py`):
```python
def test_fallback_on_invalid_model()
def test_fallback_on_api_error()
def test_fallback_preserves_context()
```

### Real-World Tests

**Issue #504 Test**:
- Run with Gemini 2.5 Flash (all stages)
- Run with Grok Code Fast 1 (all stages)
- Run with Mixed (Gemini planning → Claude building → GPT reviewing)

**Comparison Test**:
- Same issue (#504) with 3 different models
- Measure: cost, speed, quality, completion rate
- Document results

---

## Cost Optimization Strategies

### Strategy 1: Task-Based Model Selection

**Principle**: Match model capability to task complexity

**Implementation**:
```yaml
# Simple tasks → Fast/cheap models
- name: linting
  model: google/gemini-2.5-flash  # $0.0001/req

- name: pr_description
  model: x-ai/grok-code-fast-1    # Fast & cheap

# Complex tasks → Quality models
- name: architecture_design
  model: anthropic/claude-opus-4  # $15/M tokens (input)

- name: refactoring
  model: openai/gpt-4-turbo       # $10/M tokens
```

**Expected Savings**: 60-80% cost reduction vs all-Claude-Opus

---

### Strategy 2: Progressive Quality

**Principle**: Start cheap, escalate if needed

**Implementation**:
```yaml
# Stage 1: Quick planning (cheap)
- name: planning
  model: google/gemini-2.5-flash
  fallback: anthropic/claude-sonnet-4-5

# Stage 2: Quality implementation (mid-tier)
- name: building
  model: anthropic/claude-sonnet-4-5
  fallback: openai/gpt-4-turbo

# Stage 3: Independent review (different provider)
- name: reviewing
  model: openai/gpt-4-turbo
  fallback: anthropic/claude-sonnet-4-5

# Stage 4: Cheap PR text (cheap)
- name: pr_creation
  model: google/gemini-2.5-flash
```

**Expected Savings**: 40-60% vs all-Sonnet

---

### Strategy 3: Redundant Execution for Critical Stages

**Principle**: Run critical stages with multiple models, choose best

**Implementation**:
```python
# Run building stage with 2 models
claude_result = run_builder(model="claude-sonnet-4-5")
gpt_result = run_builder(model="gpt-4-turbo")

# Compare results (tests passing, code quality, etc.)
best_result = compare_and_select(claude_result, gpt_result)
```

**Cost Impact**: 2x cost for building stage, but higher quality
**Use Case**: Production releases, critical bug fixes

---

### Strategy 4: Dynamic Model Selection

**Principle**: Choose model based on issue complexity

**Implementation**:
```python
def select_model_for_issue(issue_data):
    # Analyze issue complexity
    complexity = analyze_complexity(issue_data)

    if complexity == "simple":
        return "google/gemini-2.5-flash"  # Cheap
    elif complexity == "medium":
        return "anthropic/claude-sonnet-4-5"  # Balanced
    else:  # complex
        return "anthropic/claude-opus-4"  # Quality
```

**Expected Savings**: 30-50% vs fixed model

---

## Risk Analysis & Mitigation

### Risk 1: Tool Execution Security

**Risk**: LLM generates malicious bash command (e.g., `rm -rf /`)

**Severity**: CRITICAL

**Mitigation**:
1. **Command Sandboxing**: Run bash commands in restricted environment
2. **Command Whitelist**: Only allow specific bash commands
3. **User Confirmation**: Require approval for dangerous commands
4. **Dry Run Mode**: Preview commands before execution

**Implementation**:
```python
ALLOWED_COMMANDS = ["ls", "grep", "cat", "git", "python3", "pytest"]

def execute_bash(command: str) -> str:
    # Check for dangerous patterns
    if any(pattern in command for pattern in ["rm -rf", "sudo", "> /dev"]):
        raise SecurityError("Dangerous command blocked")

    # Check command is in whitelist
    cmd_name = command.split()[0]
    if cmd_name not in ALLOWED_COMMANDS:
        raise SecurityError(f"Command {cmd_name} not in whitelist")

    # Execute in restricted sandbox
    return subprocess.run(command, shell=True, capture_output=True,
                         timeout=30, cwd=safe_cwd)
```

---

### Risk 2: Infinite Tool Calling Loop

**Risk**: LLM keeps calling tools infinitely (never reaches final answer)

**Severity**: HIGH

**Mitigation**:
1. **Max Iterations**: Limit tool calling loop to N iterations (e.g., 10)
2. **Timeout**: Set overall timeout for stage execution
3. **Cost Circuit Breaker**: Stop if cost exceeds threshold
4. **Progress Detection**: Stop if no progress being made

**Implementation**:
```python
MAX_TOOL_ITERATIONS = 10
MAX_STAGE_COST = 0.50  # $0.50

def invoke_agent_with_tools(...):
    iterations = 0
    total_cost = 0.0

    while True:
        iterations += 1
        if iterations > MAX_TOOL_ITERATIONS:
            raise ToolLoopError("Exceeded max tool iterations")

        if total_cost > MAX_STAGE_COST:
            raise CostLimitError("Exceeded cost budget")

        # ... tool execution ...
```

---

### Risk 3: Model Format Incompatibility

**Risk**: Model doesn't support tool calling as expected

**Severity**: MEDIUM

**Mitigation**:
1. **Provider Capability Detection**: Check if model supports tools before using
2. **Graceful Degradation**: Fall back to text-only mode if tools fail
3. **Format Validation**: Validate tool call responses
4. **Explicit Model Whitelist**: Only use known-good models

**Implementation**:
```python
# Check model supports tools
if not provider.supports_tools():
    logger.warning(f"Model {model} doesn't support tools, using text-only")
    return invoke_without_tools(...)

# Validate tool call response
try:
    tool_calls = parse_tool_calls(response)
except ParseError:
    logger.error("Failed to parse tool calls, falling back")
    return invoke_with_fallback_model(...)
```

---

### Risk 4: Cross-Provider Context Loss

**Risk**: Switching models mid-pipeline loses important context

**Severity**: MEDIUM

**Mitigation**:
1. **Explicit Handoff Prompts**: Add context summary when switching models
2. **Context Preservation**: Save full conversation history
3. **State Artifacts**: Write intermediate state to files (.tac/)
4. **Validation**: Check next stage has necessary context

**Implementation**:
```python
def switch_to_next_stage(current_stage, next_stage):
    # Generate handoff summary
    summary = f"""
    # Context from {current_stage} stage:

    ## Decisions Made:
    {extract_decisions(current_stage_output)}

    ## Files Created:
    {list_files_created()}

    ## Next Steps:
    {extract_next_steps()}
    """

    # Include in next stage prompt
    next_stage_prompt = summary + original_prompt
    return next_stage_prompt
```

---

## Success Criteria

### Minimum Viable Product (MVP)

**Must Have**:
- ✅ Tool calling works with OpenRouter (any model)
- ✅ Basic tools implemented: bash, read, write
- ✅ Tool execution loop functional
- ✅ Can complete issue #504 end-to-end with Gemini
- ✅ Can complete issue #504 end-to-end with Grok
- ✅ Documentation updated

**Nice to Have**:
- ⚠️ Direct API support (Anthropic, OpenAI)
- ⚠️ Advanced tools: grep, glob, git
- ⚠️ Command sandboxing
- ⚠️ Cost circuit breakers

---

### Full Product

**Must Have** (MVP +):
- ✅ All direct APIs support tools (not just OpenRouter)
- ✅ Security sandboxing for bash commands
- ✅ Cost and iteration limits
- ✅ Mixed-model workflows tested
- ✅ Fallback mechanism validated
- ✅ Comprehensive test suite
- ✅ Production-ready error handling

**Nice to Have**:
- ⚠️ Dynamic model selection based on complexity
- ⚠️ Redundant execution for critical stages
- ⚠️ Cost optimization dashboard
- ⚠️ Quality comparison reports

---

## Implementation Timeline

### Estimate: 15-20 hours total

**Week 1** (MVP):
- Phase 1: Tool Manager Foundation (2-3 hours)
- Phase 2: OpenRouter Tool Calling (3-4 hours)
- Phase 3: Tool Execution Loop (2-3 hours)
- **Deliverable**: Working tool calling via OpenRouter ✅

**Week 2** (Full Product):
- Phase 4: Direct API Support (4-5 hours)
- Phase 5: Integration & Testing (3-4 hours)
- **Deliverable**: Production-ready multi-provider system ✅

**Week 3** (Polish):
- Security hardening
- Cost optimization
- Documentation
- Performance tuning

---

## Next Steps - Immediate Actions

### Before Writing Code

**Questions to Answer**:

1. **Primary Use Case**:
   - Is mixing models within ONE pipeline run the main goal?
   - Or testing different models on separate runs?
   - Or both?

2. **Security Tolerance**:
   - Can we run bash commands unrestricted?
   - Do we need sandboxing?
   - Should we whitelist commands?

3. **Cost Budget**:
   - What's acceptable cost per issue?
   - Should we implement cost circuit breakers?
   - How important is cost vs quality?

4. **Implementation Priority**:
   - MVP first (OpenRouter only)?
   - Or full implementation (all APIs)?
   - Time available?

### After Answers

**Start with**:
1. Create Tool Manager (Phase 1)
2. Test with simple example (not full pipeline)
3. Validate tool execution works
4. Then integrate into pipeline

---

## References

### Documentation Reviewed
- OpenAI Function Calling API (2024)
- Anthropic Claude Tool Use API (2024)
- Google Gemini Function Calling (2024)
- OpenRouter Tool Calling Documentation
- LangChain Tool Calling Abstraction

### Code Examples
- OpenRouter tool calling demo (GitHub)
- LangChain standardized tool calling
- Unified-AI-Router multi-provider example

### Research Papers
- "Unified Tool Integration for LLMs: A Protocol-Agnostic Approach" (arXiv)

---

**Document Status**: COMPLETE - Ready for Review & Discussion
**Next Action**: Review with user, answer questions, finalize approach
**Then**: Begin Phase 1 implementation

