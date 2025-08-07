# Claude Code Subagent Design Best Practices

## Executive Summary

This document provides comprehensive guidelines for creating highly effective Claude Code subagents based on research from Anthropic's official documentation, community best practices, and real-world production systems. These principles are specifically tailored for the circuit-synth project's agent ecosystem.

---

## Core Design Principles

### 1. Single Responsibility Principle
Each agent should have **one clear, focused mission**. Avoid creating "Swiss Army knife" agents that try to do everything. Focused agents:
- Are easier to invoke correctly
- Provide more predictable results
- Preserve context more efficiently
- Can be composed into powerful workflows

### 2. Explicit Expertise Declaration
Agents must clearly state their expertise domains using:
- **Role definition**: "You are a [specific expert role]..."
- **Capability boundaries**: What the agent can and cannot do
- **Domain knowledge**: Specific technical areas of expertise
- **Tool proficiency**: Which tools the agent excels at using

### 3. Structured Prompt Architecture

Every agent prompt should follow this structure:

```markdown
## IDENTITY & ROLE
[Clear role definition and expertise statement]

## CORE CAPABILITIES
[Bullet-pointed list of specific capabilities]

## KNOWLEDGE DOMAINS
[Technical areas and specialized knowledge]

## BEHAVIORAL GUIDELINES
[How the agent should approach tasks]

## WORKFLOW PATTERNS
[Step-by-step processes the agent follows]

## OUTPUT STANDARDS
[Expected format and quality of outputs]

## CONSTRAINTS & LIMITATIONS
[What the agent should NOT do]
```

---

## Effective Prompt Engineering Techniques

### 1. Clarity Over Brevity
- Be explicit about expectations
- Use clear, unambiguous language
- Define technical terms when necessary
- Provide complete context

### 2. Examples Over Rules
Instead of: "Generate good code"
Use: "Generate code following this pattern: [specific example]"

### 3. Structured Instructions
Break complex instructions into:
- **Numbered steps** for sequential processes
- **Bullet points** for parallel considerations
- **Hierarchical sections** for nested concepts
- **Clear headers** for topic organization

### 4. Edge Case Handling
Explicitly address:
- Common failure scenarios
- Ambiguous situations
- Error recovery procedures
- Escalation paths

---

## Agent Interaction Patterns

### 1. Thinking Mode Activation
Use trigger words to activate extended reasoning:
- `"think"` - Basic extended thinking
- `"think hard"` - Moderate analysis
- `"think harder"` - Deep analysis
- `"ultrathink"` - Maximum reasoning budget

### 2. Delegation Patterns
Effective agents should:
- Know when to delegate to other specialists
- Provide clear handoff context
- Maintain workflow continuity
- Aggregate results from multiple agents

### 3. Verification Workflows
Include instructions for:
- Self-validation of outputs
- Cross-checking with other agents
- Testing generated solutions
- Iterative improvement cycles

---

## Circuit-Synth Specific Guidelines

### 1. Manufacturing Awareness
All circuit design agents should consider:
- Component availability (JLCPCB stock)
- Manufacturing constraints (DFM rules)
- Cost optimization strategies
- Alternative component options

### 2. Code Generation Standards
Circuit code agents must:
- Follow circuit-synth Python patterns
- Include proper KiCad symbol/footprint references
- Add manufacturing metadata (part numbers, stock)
- Generate syntactically correct, runnable code

### 3. Validation Requirements
Every circuit-related agent should:
- Verify component compatibility
- Check electrical specifications
- Validate manufacturing feasibility
- Test code execution

---

## Performance Optimization

### 1. Model Selection Strategy
Assign agents to appropriate models based on task complexity:

| Complexity | Model | Use Cases |
|------------|-------|-----------|
| **Low** | Haiku | Simple lookups, basic formatting, documentation |
| **Medium** | Sonnet | Code generation, standard development tasks |
| **High** | Opus | Architecture design, complex debugging, security |

### 2. Tool Permission Management
Grant only necessary tools:
- Minimize tool access for security
- Reduce decision complexity
- Improve response speed
- Prevent unintended actions

### 3. Context Preservation
Design agents to:
- Minimize token usage in prompts
- Focus on essential information
- Use references instead of repetition
- Delegate detail work to subagents

---

## Common Anti-Patterns to Avoid

### ❌ DON'T: Create Vague Agents
```markdown
"You are a helpful assistant that can do many things..."
```

### ✅ DO: Create Specific Experts
```markdown
"You are a SPICE simulation expert specializing in analog circuit validation using PySpice..."
```

### ❌ DON'T: Mix Multiple Responsibilities
```markdown
"You handle circuit design, testing, documentation, and deployment..."
```

### ✅ DO: Focus on Single Domain
```markdown
"You are a circuit test plan specialist focused exclusively on generating comprehensive test procedures..."
```

### ❌ DON'T: Use Ambiguous Instructions
```markdown
"Try to make good circuits that work well..."
```

### ✅ DO: Provide Clear Directives
```markdown
"Generate production-ready circuit-synth Python code that:
1. Uses verified KiCad symbols from standard libraries
2. Includes JLCPCB part numbers for all components
3. Follows proper decoupling capacitor placement..."
```

---

## Testing and Validation

### 1. Agent Testing Checklist
- [ ] Single responsibility verified
- [ ] Clear expertise boundaries defined
- [ ] Structured prompt format followed
- [ ] Examples provided for complex tasks
- [ ] Edge cases explicitly handled
- [ ] Delegation patterns documented
- [ ] Output standards specified
- [ ] Tool permissions appropriate

### 2. Performance Metrics
Monitor and optimize:
- **Response accuracy**: Does the agent solve the intended problem?
- **Context efficiency**: How much context does the agent consume?
- **Delegation effectiveness**: Does the agent appropriately use other agents?
- **Error handling**: How well does the agent recover from failures?

### 3. Iterative Improvement
- Collect real-world usage patterns
- Identify common failure modes
- Refine prompts based on performance
- Update examples with actual use cases
- Document lessons learned

---

## Implementation Workflow

### Phase 1: Design
1. Define agent's single responsibility
2. Identify required expertise domains
3. Determine necessary tools
4. Draft structured prompt

### Phase 2: Implementation
1. Create agent file with proper YAML frontmatter
2. Write comprehensive system prompt
3. Configure tool permissions
4. Register in mcp_settings.json

### Phase 3: Testing
1. Test core functionality
2. Verify delegation patterns
3. Check edge case handling
4. Validate output quality

### Phase 4: Optimization
1. Monitor real-world performance
2. Collect user feedback
3. Refine prompt based on usage
4. Update documentation

---

## Quick Reference: Agent Prompt Template

```markdown
---
name: agent-name
description: One-line description of agent's purpose
tools: ["Tool1", "Tool2"] # Or ["*"] for all tools
---

You are a [specific role] specializing in [domain expertise].

## CORE EXPERTISE
[2-3 sentences defining deep expertise areas]

## PRIMARY CAPABILITIES
- [Specific capability 1]
- [Specific capability 2]
- [Specific capability 3]

## TECHNICAL KNOWLEDGE
### [Knowledge Domain 1]
- [Specific expertise point]
- [Specific expertise point]

### [Knowledge Domain 2]
- [Specific expertise point]
- [Specific expertise point]

## WORKFLOW METHODOLOGY
### 1. [First Phase Name]
- [Specific step]
- [Specific step]

### 2. [Second Phase Name]
- [Specific step]
- [Specific step]

## OUTPUT STANDARDS
- [Quality requirement 1]
- [Quality requirement 2]
- [Format requirement]

## OPERATIONAL CONSTRAINTS
- [Limitation 1]
- [Limitation 2]
- [Boundary condition]

## DELEGATION TRIGGERS
When encountering [situation], delegate to [other-agent] for [specific task].

## EXAMPLE PATTERNS
[Provide 1-2 concrete examples of ideal behavior/output]
```

---

## Conclusion

Effective Claude Code subagents are:
- **Focused**: Single responsibility with clear boundaries
- **Explicit**: Detailed expertise and capability declarations
- **Structured**: Well-organized prompts with clear sections
- **Practical**: Include examples and concrete patterns
- **Collaborative**: Know when and how to delegate
- **Validated**: Tested and optimized based on real usage

By following these best practices, circuit-synth agents will provide reliable, high-quality assistance for complex electronic design tasks while maintaining efficiency and context preservation.

---

*Last Updated: 2025-08-06*
*Version: 1.0*
*Author: Circuit-Synth Development Team*