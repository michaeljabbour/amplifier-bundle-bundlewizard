# Three-Level Convergence Criteria

Every bundle produced by bundlewizard must pass all three levels before delivery. There are no shortcuts. "Simple" bundles are where the bugs hide.

## Convergence Formula

```
converged = (level_1 == PASS) AND (level_2 >= 0.85) AND (level_3 >= 0.80)
```

Level 2 bar is higher because philosophical violations are objective. Level 3 is lower because functional evaluation involves expert judgment.

---

## Level 1: Structural (pass/fail gates)

All gates must pass. If ANY gate fails, convergence score is 0. Fix structural issues before evaluating anything else.

| Gate | Check | How To Verify |
|------|-------|--------------|
| Bundle loads | `bundle.md` frontmatter parses as valid YAML | `python3 -c "import yaml; yaml.safe_load(open('bundle.md').read().split('---')[1])"` |
| Agent references resolve | Every agent in `behaviors/*.yaml` → `agents.include` has a corresponding file | Cross-reference `agents/` directory against behavior |
| URI syntax valid | All `source:` and `includes:` URIs match `git+https://...@tag` format | Regex check on all YAML files |
| No duplicate context | No context file is loaded by BOTH `context.include` AND an agent `@mention` in the same session | Manual review of behavior + agent @mentions |
| Source URIs reachable | Module/bundle source repos exist (at least structurally valid) | URI format validation (don't HTTP check during generation) |
| Mode references valid | All mode files in `modes/` are discoverable by hooks-mode | Check `search_paths` config in behavior |

**If Level 1 fails:** Stop. Fix the structural issue. Do not evaluate Level 2 or 3.

---

## Level 2: Philosophical (scored rubric, 0.0 – 1.0)

Four criteria, equally weighted at 25% each. Threshold: **0.85**.

### 2a. Thin Bundle Pattern (25%)

| Score | Criteria |
|-------|----------|
| 1.0 | bundle.md ≤20 lines frontmatter, no @mentions in body, no redeclaration |
| 0.75 | Minor violation: frontmatter slightly over 20 lines but no content duplication |
| 0.5 | Moderate violation: @mentions in bundle.md body or some redeclaration |
| 0.0 | bundle.md is a monolith with inline agent descriptions or heavy context |

### 2b. Context Sink Discipline (25%)

| Score | Criteria |
|-------|----------|
| 1.0 | Root context ≤2 files, no file >100 lines at root, agents @mention only what they need |
| 0.75 | Root context has 3 files or one root file slightly over 100 lines |
| 0.5 | Multiple heavy files at root or agents @mentioning everything |
| 0.0 | All context loaded at root level; agents are empty shells |

### 2c. Agent Description Quality (25%)

| Score | Criteria |
|-------|----------|
| 1.0 | Every agent has WHY/WHEN/WHAT/HOW, 2+ examples with `<example>` tags |
| 0.75 | All agents have descriptions but some missing examples or unclear trigger |
| 0.5 | Some agents have good descriptions, others are vague one-liners |
| 0.0 | Agent descriptions are perfunctory ("Handles X") |

### 2d. Composition Hygiene (25%)

| Score | Criteria |
|-------|----------|
| 1.0 | No circular includes, behaviors reusable, sources appropriately pinned, one behavior per concern |
| 0.75 | Minor: one source using @main that should be pinned, but no structural issues |
| 0.5 | Behavior does too many things or has hardcoded paths |
| 0.0 | Circular includes, duplicate declarations, or fundamentally broken composition |

### Level 2 Score Calculation

```
level_2 = (thin_pattern * 0.25) + (context_sink * 0.25) + (agent_quality * 0.25) + (composition * 0.25)
```

**If Level 2 < 0.85:** Iterate. The critic identifies which criteria scored low. The refiner targets those specific issues.

---

## Level 3: Functional (domain-specific, scored 0.0 – 1.0)

Threshold: **0.80**.

Evaluates whether the bundle actually does what the user intended. This varies by what the bundle is FOR:

| Bundle Type | Functional Check |
|------------|-----------------| 
| Code review bundle | Does it review code? Delegate a sample review task. |
| Mode bundle | Do modes activate? Do tool permissions work? |
| Agent bundle | Do agents respond to their trigger conditions? |
| Workflow bundle | Does the recipe pipeline complete? |
| General bundle | Does the primary use case work end-to-end? |

The evaluator delegates to the appropriate **domain expert** for functional assessment. Bundlewizard does NOT judge domain fitness itself.

### Functional Score Breakdown

| Score | Criteria |
|-------|----------|
| 1.0 | Primary use case works, edge cases handled, no broken paths |
| 0.80 | Primary use case works, some edge cases need attention |
| 0.60 | Primary use case partially works, significant gaps |
| 0.0 | Bundle does not achieve its stated purpose |

---

## Loop Discipline

1. **Evaluate after every refinement** — Never batch multiple refinements before evaluating.
2. **checkpoint_best** — Save the highest-scoring iteration. If convergence stalls, deliver the best achieved.
3. **Patience counter** — If score hasn't improved in 3 iterations, trigger diagnosis: are we refining the right things?
4. **Never silently declare done** — Convergence is a measured state, not a feeling.
