---
name: prompt-improver
description: Improve vague, ambiguous, incomplete, or unfocused prompts without changing the user's intent. Use when the user asks to improve, rewrite, refine, sharpen, clarify, or structure a prompt for another AI system.
---

# Prompt Improver

## Quick Start

Use this skill to rewrite a prompt so it is easier for another AI system to execute reliably.

Priorities:
- Preserve the user's intent
- Increase clarity and specificity
- Add missing structure only when justified
- Avoid inventing facts, constraints, or goals

## When To Use

Use this skill when:
- the prompt is vague or ambiguous
- the prompt lacks context, audience, or success criteria
- the task is overly broad or unfocused
- the user wants better wording for another AI system
- the user wants a structured prompt with clear sections

Do not use this skill when:
- the prompt is already precise and well-scoped
- the user explicitly wants the wording preserved
- the task is to answer the prompt directly rather than improve it

## Input

Use the user's prompt plus any optional context they provide, such as:

```yaml
prompt: <original prompt>
goal: <desired outcome>
constraints: <restrictions or requirements>
output_format: <preferred response format>
audience: <target reader or user>
```

Treat omitted fields as unknown, not as permission to guess.

## Improvement Workflow

### 1. Identify Intent

Infer the user's actual objective before rewriting.

Check:
- What task is the user trying to get done?
- What output would count as success?
- What details are essential versus optional?

### 2. Diagnose Prompt Problems

Look for:
- ambiguity
- missing context
- missing constraints
- missing output format
- scope that is too broad or too narrow
- verbose wording that hides the request

### 3. Rewrite With Structure

Prefer this structure when it improves execution:
- Task
- Context
- Constraints
- Output Format
- Tone or Style

Use only the sections that help. Do not force all sections into every prompt.

### 4. Preserve Intent

The improved prompt must:
- keep the original meaning
- avoid introducing unsupported assumptions
- avoid changing the requested task
- stay as concise as possible while remaining clear

### 5. Surface Remaining Unknowns

If critical information is still missing, include a short list of optional clarifying questions after the improved prompt.

## Response Format

Return:

```markdown
## Improved Prompt
<rewritten prompt>

## Improvements Made
- <specific improvement>
- <specific improvement>

## Optional Clarifying Questions
- <question if needed>
```

If no clarifying questions are needed, say `None`.

## Quality Bar

Before finalizing, verify:
- the rewritten prompt is clearer than the original
- the user's intent is unchanged
- no new factual claims were introduced
- the structure matches the task
- the output can be pasted directly into another AI system

## Additional Resources

- For example transformations, see [examples.md](examples.md)
