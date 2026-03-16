---
name: bundle-reference
description: "Complete reference tables for Bundlewizard modes, agents, recipes, output tiers, and anti-patterns"
---

## Reference: The Bundlewizard Pipeline

The full bundle development workflow:

```
/bundle-explore  -->  interview summary + routing decision (create new / improve existing)
       |
/bundle-spec     -->  bundle spec (tier, file structure, components, delegation map)
       |
/bundle-plan     -->  implementation plan (file order or renovation tasks)
       |
/bundle-execute  -->  bundle artifacts (generate/critique/refine per iteration)
       |         ^
       |         | (convergence loop via recipe)
       v         |
/bundle-verify   -->  evidence: Level 1 PASS, Level 2 ≥0.85, Level 3 ≥0.80
       |
/bundle-finish   -->  packaged artifact (behavior, bundle, or application bundle)
```

At any point, if something goes wrong: `/bundle-debug` (systematic diagnosis).

**Two-track UX:**
- **Interactive** — work through modes manually, human judgment at each step
- **Recipe** — use `bundle-development-cycle.yaml` with approval gates at critical junctures

Both tracks produce the same artifact. The recipe just automates mode transitions.

---

## Reference: Modes

| Mode | Shortcut | Purpose | Who Does The Work | Tool Permissions Summary |
|------|----------|---------|-------------------|-----------------------------|
| Explore | `/bundle-explore` | Interview the user, route to create or improve path | bundle-explorer agent | read_file: safe, bash: warn, write: BLOCKED |
| Spec | `/bundle-spec` | Design the bundle composition, produce bundle-spec.md | bundle-spec-writer agent | read_file: safe, bash: warn, write: warn |
| Plan | `/bundle-plan` | Break spec into ordered implementation tasks | bundle-plan-writer agent | read_file: safe, bash: warn, write: warn |
| Execute | `/bundle-execute` | Orchestrate generate/critique/refine pipeline | dispatch agents only | read_file: safe, delegate: safe, recipes: safe, write: BLOCKED |
| Verify | `/bundle-verify` | Independent three-level convergence assessment | bundle-evaluator agent | read_file: safe, bash: safe, write: warn |
| Finish | `/bundle-finish` | Version stamp, git, deliver the artifact | bundle-packager agent | read_file: safe, bash: safe, write: safe |
| Debug | `/bundle-debug` | Diagnose issues at any pipeline stage | main agent (you) | read_file: safe, bash: safe, write: BLOCKED |
| Skip Permissions | `/dangerously-skip-permissions` | Autonomous self-evolution — all approval gates bypassed | autonomous | everything: safe/allow |

**Mode transition graph (allowed_transitions):**

| From | Allowed Next Modes |
|------|---------------------|
| bundle-explore | bundle-spec, bundle-debug |
| bundle-spec | bundle-plan, bundle-explore, bundle-debug |
| bundle-plan | bundle-execute, bundle-spec, bundle-debug |
| bundle-execute | bundle-verify, bundle-debug |
| bundle-verify | bundle-finish, bundle-debug, bundle-execute |
| bundle-finish | (none — terminal mode, `allow_clear: true`) |
| bundle-debug | bundle-explore, bundle-spec, bundle-plan, bundle-execute, bundle-verify, bundle-finish |
| dangerously-skip-permissions | all modes, `allow_clear: true` |

---

## Reference: Agents

| Agent | Role | When to Use | Model Role |
|-------|------|-------------|------------|
| `bundlewizard:bundle-explorer` | Interview + routing fork + experience detection | MANDATORY — first agent in every session | reasoning, general |
| `bundlewizard:bundle-auditor` | Full three-level audit of existing bundles | Only in "improve existing" path — dispatched by explorer | critique, general |
| `bundlewizard:ecosystem-scout` | Ecosystem survey, find reusable components | During exploration — dispatched by explorer | research, general |
| `bundlewizard:bundle-spec-writer` | Composition design → bundle-spec.md | After interview — delegate document creation | reasoning, general |
| `bundlewizard:bundle-plan-writer` | Implementation plan from spec | After spec approved — delegate plan creation | reasoning, general |
| `bundlewizard:bundle-generator` | Writes bundle artifacts (YAML, markdown, files) | Every generate step in /bundle-execute — NEVER called directly | coding, general |
| `bundlewizard:bundle-critic` | Adversarial review with context_depth="none" | Every critique step in /bundle-execute | critique, general |
| `bundlewizard:bundle-refiner` | Targeted fixes from critic feedback (no scope creep) | Every refine step (when critique says NEEDS CHANGES) | coding, general |
| `bundlewizard:bundle-evaluator` | Three-level convergence scoring | After every iteration + /bundle-verify | critique, general |
| `bundlewizard:bundle-packager` | Version stamp, git init/branch, deliver | Terminal step in /bundle-finish | fast |

**Fresh agent per task:** Use `context_depth="none"` for generator/critic/refiner. Clean context = focused attention = quality output.

---

## Reference: Recipes

| Recipe | Pattern Type | When to Use |
|--------|-------------|-------------|
| `bundlewizard:recipes/bundle-single-iteration.yaml` | Sub-recipe, sequential 4-step pipeline | Invoked by refinement-loop only — not for direct use |
| `bundlewizard:recipes/bundle-refinement-loop.yaml` | While-loop convergence (max 10 iterations) | When you need the autonomous generate/critique/refine loop |
| `bundlewizard:recipes/bundle-development-cycle.yaml` | Staged recipe, 3 approval gates | Full interactive cycle: explore → spec → plan → execute → verify → finish |
| `bundlewizard:recipes/bundle-batch-generation.yaml` | Foreach batch recipe | Batch generation for multiple bundles using STATE.yaml |
| `bundlewizard:recipes/bundle-audit.yaml` | Flat sequential recipe | Standalone audit of an existing bundle — evaluation only, no generation |

---

## Reference: Output Tiers

| Tier | What It Is | When It's Right | Example |
|------|-----------|----------------|---------|
| **Behavior** | Reusable capability package (YAML + context + maybe agents). Composed via `includes:`. | Adding a capability to an existing bundle | A logging behavior, a mode system, a tool mount |
| **Bundle** | Standalone with bundle.md, behaviors, agents, context. A complete product. | A focused tool/capability that stands alone | A code review bundle, a git helper bundle |
| **Application Bundle** | Full-featured with modes, recipes, skills, possibly modules. | A complete workflow or domain system | harness-machine, superpowers, bundlewizard itself |

Size is emergent from scope, not a design input. Never pad a behavior into a bundle for perceived importance.

---

## Reference: Convergence Criteria Summary

```
converged = (Level 1 == PASS) AND (Level 2 ≥ 0.85) AND (Level 3 ≥ 0.80)
```

| Level | What It Checks | Type | Threshold |
|-------|---------------|------|-----------|
| Level 1: Structural | Bundle loads, agent refs resolve, URIs valid, no duplicate context | pass/fail gates | ALL must PASS |
| Level 2: Philosophical | Thin pattern, context sinks, agent descriptions, composition hygiene | scored rubric (4×25%) | ≥ 0.85 |
| Level 3: Functional | Does it do what the spec says? Domain-expert evaluated. | scored assessment | ≥ 0.80 |

**Loop discipline:**
- Evaluate after every refinement — never batch fixes
- checkpoint_best after every improvement — never lose progress
- Max 10 iterations for bundles (vs 60 for constraint code)
- On timeout: deliver checkpoint_best with a note about what didn't converge

---

## Reference: Anti-Rationalization Table

| Your Excuse | Why It's Wrong | What You MUST Do |
|-------------|----------------|-----------------|
| "I'll just write the bundle.md directly, it's only 14 lines" | The pattern.md double-load bug was exactly 1 line. Generator + critic caught it. You wouldn't have. | Delegate to bundle-generator. Critic reviews it. Every time. |
| "The fix is obvious, skip the critic" | Critic runs with context_depth="none". It sees what you can't because it doesn't share your assumptions. | Always run generate → critique → refine → assess in order. |
| "This is a simple behavior, skip the evaluator" | "Simple" is where bugs hide. Simple artifacts are under-scrutinized by default. | Evaluate after every refinement. checkpoint_best. |
| "I know what the expert would say" | The expert loads authoritative context (foundation docs, ecosystem knowledge). Your guess is based on incomplete session context. | Delegate. The expert has @mentioned docs you don't. |
| "One more quick fix, then we'll evaluate" | Batching fixes before evaluation means you can't attribute score changes to specific fixes. | Evaluate after every refinement. One fix, one evaluation. |
| "The bundle is simple enough to skip the convergence loop" | Every generated bundle goes through the loop. No exceptions. | Use /bundle-execute and the recipe pipeline. |
| "I'll pin the source URIs before release" | You'll forget. Or someone will ship @main to production. | Pin now, or add `# TODO: pin before release` and flag in critique. |

---

## Reference: Key Commands

```bash
# Run full interactive cycle (create new)
amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml \
  with bundle_description='a bundle that helps with code review' \
  output_dir='~/dev/amplifier-bundle-code-review' \
  path='create'"

# Run full interactive cycle (improve existing)
amplifier run "execute bundlewizard:recipes/bundle-development-cycle.yaml \
  with bundle_description='improve code review bundle' \
  output_dir='~/dev/amplifier-bundle-code-review' \
  path='~/dev/amplifier-bundle-code-review'"

# Standalone audit of existing bundle
amplifier run "execute bundlewizard:recipes/bundle-audit.yaml \
  with bundle_path='~/dev/my-existing-bundle'"

# Batch factory generation
amplifier run "execute bundlewizard:recipes/bundle-batch-generation.yaml \
  with targets=['code-review helper','git worktree manager'] \
  state_yaml_path=output/STATE.yaml \
  output_dir=output/bundles"

# Check pending approvals (staged recipes)
amplifier run "list pending approvals"

# Approve and resume
amplifier run "approve recipe session <session-id> stage exploration"
amplifier run "resume recipe session <session-id>"
```
