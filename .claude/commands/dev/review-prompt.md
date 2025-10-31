---
name: review-prompt
description: Review prompts for best practices and clarity
---

You are receiving a request to review a prompt, instructions, or documentation for best practices and clarity.

## Your Task

Launch a **Haiku 4.5 agent** using the Task tool to perform a comprehensive prompt review. The agent should analyze the provided content for:

1. **Prompt Engineering Best Practices** - Clarity, specificity, structure, completeness, actionability
2. **Assumed Information Detection** - Implicit context, undefined terms, missing background
3. **Perspective and Bias Analysis** - Point of view consistency, audience assumptions, tone appropriateness
4. **Common Prompt Problems** - Verbosity, AI slop, vagueness, contradictions, missing examples
5. **Quality Improvements** - Conciseness, clarity enhancements, structural improvements

## How to Execute This Command

When this command is invoked, you MUST:

1. **Identify the target content** to review:
   - If user provides a file path (like `@CLAUDE.md` or `@.claude/agents/circuit-architect.md`), read that file
   - If user provides inline text, use that text directly
   - If neither is provided, ask the user what they want reviewed

2. **Launch a Haiku agent** using the Task tool with `subagent_type="general-purpose"` and `model="haiku"`

3. **Provide the agent** with comprehensive instructions to perform the analysis described in this document

## Usage Examples
```bash
/dev:review-prompt @CLAUDE.md
/dev:review-prompt @.claude/commands/dev/review-branch.md
/dev:review-prompt @.claude/agents/circuit-architect.md
/dev:review-prompt "inline prompt text here"
```

## What This Does

This command launches a fast, specialized Haiku 4.5 agent to perform comprehensive prompt review with focus on:

### 1. Prompt Engineering Best Practices
- **Clarity**: Is the prompt clear and unambiguous?
- **Specificity**: Does it provide concrete examples and specific requirements?
- **Structure**: Is it well-organized with logical flow?
- **Completeness**: Does it include all necessary context?
- **Actionability**: Are instructions clear and executable?

### 2. Assumed Information Detection
- **Implicit Context**: Information assumed to be known but never stated
- **Undefined Terms**: Technical terms or jargon used without definition
- **Missing Background**: Context that would help understanding
- **Unstated Requirements**: Prerequisites not explicitly mentioned
- **Hidden Dependencies**: Relationships or dependencies not made clear

### 3. Perspective and Bias Analysis
- **Point of View**: Is the perspective consistent and appropriate?
- **Audience Assumptions**: Does it assume specific audience knowledge?
- **Cultural Context**: Any culturally-specific references that may not translate?
- **Accessibility**: Is it accessible to the intended audience?
- **Tone Appropriateness**: Is the tone suitable for the purpose?

### 4. Common Prompt Problems
- **Verbosity**: Unnecessarily long or repetitive content
- **AI Slop**: Over-enthusiastic or marketing-speak language
- **Vagueness**: Unclear instructions or ambiguous requirements
- **Contradictions**: Conflicting instructions or information
- **Scope Creep**: Trying to accomplish too much in one prompt
- **Missing Examples**: Lacking concrete demonstrations
- **Poor Formatting**: Hard to read or poorly structured

### 5. Quality Improvements
- **Conciseness**: Suggestions to make it more concise
- **Clarity Enhancements**: Ways to make instructions clearer
- **Example Additions**: Where examples would help
- **Structure Improvements**: Better organization suggestions
- **Terminology Clarification**: Terms that need definition

## Output Structure

The agent will provide a structured review report:

```markdown
# Prompt Review Report

## Executive Summary
- Overall Quality Score: X/10
- Key Strengths: [bullet points]
- Critical Issues: [bullet points]
- Quick Wins: [easy improvements]

## Detailed Analysis

### 1. Best Practices Assessment
- ✅ **Strengths**: What's working well
- ⚠️ **Issues**: What needs improvement
- 💡 **Suggestions**: Specific recommendations

### 2. Assumed Information
- **Implicit Assumptions**: [list with examples]
- **Missing Definitions**: [terms needing explanation]
- **Context Gaps**: [background info needed]
- **Recommended Additions**: [what to add and where]

### 3. Perspective Analysis
- **Current Perspective**: [description]
- **Consistency**: [assessment]
- **Audience Alignment**: [how well it matches intended audience]
- **Tone Analysis**: [professional/casual/technical/etc.]
- **Bias Detection**: [any identified biases]

### 4. Problem Areas
#### Clarity Issues
- [Specific unclear sections with line references]

#### Completeness Gaps
- [Missing information with impact assessment]

#### Structural Problems
- [Organization or flow issues]

#### Terminology Issues
- [Undefined or confusing terms]

### 5. Recommended Improvements

#### High Priority (Critical for effectiveness)
1. [Specific actionable improvement]
2. [Specific actionable improvement]

#### Medium Priority (Enhance clarity)
1. [Specific actionable improvement]
2. [Specific actionable improvement]

#### Low Priority (Polish and refinement)
1. [Specific actionable improvement]
2. [Specific actionable improvement]

### 6. Rewrite Suggestions
For the most critical sections, the agent may provide rewritten versions:

**Original:**
```
[problematic section]
```

**Improved:**
```
[clearer, better version]
```

**Why This is Better:**
- [Explanation of improvements]

## Quality Metrics
- Clarity Score: X/10
- Completeness Score: X/10
- Structure Score: X/10
- Actionability Score: X/10
- Accessibility Score: X/10

## Final Recommendation
[Overall assessment and primary action items]
```

## Example Usage

### Review a CLAUDE.md file
```bash
/dev:review-prompt @CLAUDE.md
```

### Review a slash command prompt
```bash
/dev:review-prompt @.claude/commands/dev/review-branch.md
```

### Review inline prompt text
```bash
/dev:review-prompt "You are a helpful assistant that reviews code. Please analyze the following code and provide feedback."
```

### Review agent instructions
```bash
/dev:review-prompt @.claude/agents/circuit-architect.md
```

## What the Agent Will Check

### Prompt Engineering Principles
1. **Task Clarity**: Is it clear what needs to be done?
2. **Context Sufficiency**: Is enough context provided?
3. **Constraint Specification**: Are limitations clearly stated?
4. **Example Quality**: Are examples helpful and relevant?
5. **Output Format**: Is desired output format specified?
6. **Error Handling**: How should edge cases be handled?

### Communication Quality
1. **Readability**: Easy to scan and understand?
2. **Precision**: Specific rather than vague?
3. **Consistency**: Terminology and style consistent?
4. **Flow**: Logical progression of ideas?
5. **Completeness**: All necessary information present?

### Accessibility Factors
1. **Knowledge Assumptions**: What expertise is assumed?
2. **Cultural References**: Any culture-specific content?
3. **Language Complexity**: Appropriate for audience?
4. **Technical Jargon**: Explained when used?
5. **Inclusivity**: Free from unnecessary bias?

## Integration with Development Workflow

This command is particularly useful for:

### Documentation Review
```bash
# Review README before release
/dev:review-prompt @README.md

# Review contributor guidelines
/dev:review-prompt @CONTRIBUTING.md

# Review API documentation
/dev:review-prompt @docs/api.rst
```

### Agent Development
```bash
# Review agent instructions before deployment
/dev:review-prompt @.claude/agents/new-agent.md

# Review agent prompts for clarity
/dev:review-prompt @.claude/agents/component-guru.md
```

### Command Creation
```bash
# Review new slash command before committing
/dev:review-prompt @.claude/commands/dev/new-command.md

# Validate command documentation
/dev:review-prompt @.claude/commands/dev/existing-command.md
```

### Educational Content
```bash
# Review tutorial content
/dev:review-prompt @docs/quickstart.rst

# Review example documentation
/dev:review-prompt @examples/README.md
```

## Advanced Options (Optional Extensions)

Future enhancements could include:

- `--focus=clarity` - Focus only on clarity issues
- `--focus=assumptions` - Focus on assumed information
- `--focus=perspective` - Focus on perspective and bias
- `--depth=quick` - Quick scan vs full analysis
- `--rewrite` - Provide complete rewritten version
- `--audience=beginners` - Target specific audience level
- `--format=json` - Output in machine-readable format

## Benefits

1. **Improved Communication**: Clearer, more effective prompts
2. **Reduced Ambiguity**: Fewer misunderstandings and clarifications
3. **Better Results**: More precise outputs from AI systems
4. **Accessibility**: Content accessible to wider audiences
5. **Professionalism**: Higher quality documentation and instructions
6. **Time Savings**: Catch issues before deployment

---

**This prompt review command helps maintain high-quality, clear, and accessible communication across all circuit-synth documentation, agent instructions, and development workflows.**
