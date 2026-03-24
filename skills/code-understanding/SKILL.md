---
name: code-understanding
description: Use when explaining a feature, class, function, entity, module, repository, or URL for code and system understanding. Produces a structured explanation covering overview, responsibility, structure, flow, key logic, data model, usage, constraints, pitfalls, and extension, and handles URLs by detecting whether they are code, docs, API references, or technical articles before normalizing them into the same explanation format.
---

# Code Understanding

## Overview

Use this skill when the user wants a high-quality understanding of code or system behavior rather than a line-by-line walkthrough. The goal is to turn an input such as a feature description, a class, a function, an entity, a module, a repository, or a URL into a structured explanation that helps an engineer understand purpose, boundaries, behavior, data, and extension points.

Read [references/understand-skill-system.yaml](references/understand-skill-system.yaml) when you need the exact modular skill definitions, schemas, and prompt templates.

## Supported Inputs

This skill supports:

- Feature descriptions
- Classes
- Functions
- Entities
- Modules
- Repositories
- URLs

If the input is a URL, first detect whether it points to a code repository, single file, API documentation page, or technical article. Extract the relevant structure, purpose, and logic, then normalize the result into the same explanation workflow used for direct code or system inputs.

## Output Contract

Always produce the explanation in this order:

1. Overview
2. Responsibility
3. Structure
4. Flow
5. Key Logic
6. Data Model
7. Usage
8. Constraints
9. Pitfalls
10. Extension

If a section is only weakly applicable, say so briefly instead of inventing filler.

## Working Rules

- Explain for understanding, not translation.
- Do not restate code line-by-line.
- Do not produce trivial summaries.
- Focus on design intent, important interactions, non-obvious logic, boundaries, and tradeoffs.
- Label inferences when they are not explicitly supported by the source.
- Adapt the explanation to the input type instead of forcing one rigid style.

## Adaptive Focus

- For a class, emphasize methods, fields, collaborators, lifecycle, and interactions.
- For a function, emphasize inputs, outputs, side effects, branching, and edge cases.
- For an entity, emphasize fields, invariants, identity, relationships, and constraints.
- For a feature, emphasize workflow, participating components, and end-to-end behavior.
- For a module, emphasize internal organization, public surface, and dependencies.
- For a repository, emphasize architecture, major subsystems, conventions, and integration flow.
- For URL-backed content, determine the content type first, then apply the matching strategy.

## Workflow

### 1. Normalize The Input

- Determine the true abstraction level of the input.
- Gather the minimum relevant source context needed for explanation.
- If the source is a URL, resolve and classify it before analyzing content.

### 2. Build The Explanation

Use the modular skills defined in [references/understand-skill-system.yaml](references/understand-skill-system.yaml):

- `overview`
- `responsibility`
- `structure`
- `flow`
- `key_logic`
- `data_model`
- `usage`
- `constraints`
- `pitfalls`
- `extension`

The master skill is `understand`, which orchestrates all of them and adapts the strategy based on the input type. Its output artifact is the final `explanation`.

### 3. Keep The Quality Bar High

The final explanation should help a capable engineer answer:

- What is this really?
- What does it own and what is outside its scope?
- What are the important parts?
- How does it behave over time?
- What ideas make it work?
- What data matters?
- How is it used?
- What assumptions must hold?
- Where do people get it wrong?
- How should it evolve safely?
