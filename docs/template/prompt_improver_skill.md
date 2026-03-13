# Prompt Improver Skill

## Purpose

Improve the clarity, precision, and effectiveness of a user's prompt
before it is executed by another AI system.

This skill helps users transform vague or incomplete prompts into
well-structured instructions that produce higher-quality outputs.

------------------------------------------------------------------------

# Skill: Prompt Improver

## Description

The Prompt Improver analyzes a user's prompt and rewrites it to improve:

-   clarity
-   specificity
-   structure
-   context completeness
-   instruction quality

The goal is **not to change the user's intent**, but to **express it in
a form that AI systems execute more reliably.**

------------------------------------------------------------------------

# When To Use

Use this skill when:

-   the prompt is vague
-   the prompt lacks context
-   instructions are ambiguous
-   the task could benefit from structure
-   the prompt is overly long but unfocused
-   the user is unsure how to phrase a request

Do **not** use when:

-   the prompt is already precise
-   the user explicitly asks to keep wording unchanged

------------------------------------------------------------------------

# Input

``` yaml
prompt: <user prompt>
goal: <optional explanation of desired outcome>
constraints: <optional restrictions>
output_format: <optional format preference>
```

Example:

``` yaml
prompt: explain blockchain
goal: help undergraduate students understand
constraints: keep it simple
```

------------------------------------------------------------------------

# Improvement Process

The agent performs the following steps:

### 1. Identify Intent

Determine the user's underlying objective.

Questions to infer:

-   What task is being requested?
-   What output would satisfy the user?

------------------------------------------------------------------------

### 2. Detect Issues

Check for common prompt problems:

  Issue                 Description
  --------------------- -----------------------------
  Ambiguity             unclear instructions
  Missing context       lack of audience or purpose
  Scope issues          too broad or too narrow
  Missing format        output format unspecified
  Inefficient wording   unnecessary verbosity

------------------------------------------------------------------------

### 3. Add Structure

Rewrite the prompt using the structure:

    Task
    Context
    Constraints
    Output Format
    Tone (if relevant)

------------------------------------------------------------------------

### 4. Preserve Intent

The improved prompt must:

-   keep the user's meaning
-   avoid introducing new assumptions
-   remain faithful to the original request

------------------------------------------------------------------------

# Output Format

Return the following structured response:

``` markdown
## Improved Prompt
<rewritten prompt>

## Improvements Made
- improvement 1
- improvement 2
- improvement 3

## Optional Clarifying Questions
- question 1
- question 2
```
