---
name: bundle-design
description: "Composition patterns, common mistakes, tier selection guidance, and expert delegation patterns for designing Amplifier bundles"
---

## The Thin Bundle Pattern

The most important pattern in bundle design. `bundle.md` is a router, not a knowledge base.

### Rules

| Rule | What It Means | How to Check |
|------|-------------|--------------|
| ≤20 lines YAML frontmatter | name, version, description, includes. That's it. | Count lines between `---` markers |
| NO `@mentions` in markdown body | Don't pull context files into the root session | Search for `@` in the body section |
| NO redeclaration | If a behavior provides agents, don't list them in bundle.md frontmatter | Cross-reference behavior with bundle.md |
| Markdown body is a menu | Brief description of what's available (modes, agents, recipes) | Human-readable, not machine context |

### Good Example

```yaml
---
bundle:
  name: my-bundle
  version: 0.1.0
  description: |
    Does X for Y users.

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@v1.0.0
  - bundle: my-bundle:behaviors/core
---

# My Bundle

Does X for Y users.

## Modes
| Shortcut | What It Does |
|----------|-------------|
| /my-mode | Does the thing |

## Getting Started
Tell me what you need.
```

### Bad Example

```yaml
---
bundle:
  name: my-bundle
  version: 0.1.0
  description: |
    Does X for Y users. This bundle provides comprehensive capabilities
    for managing Y workflows including A, B, C, D, E features with
    full integration into the Amplifier ecosystem and support for
    multiple deployment targets across cloud and local environments.
    It uses the factory pattern with generate/critique/refine cycles
    and supports both interactive and automated workflows.
  agents:
    - name: my-agent-1
      description: "Does thing 1"
    - name: my-agent-2
      description: "Does thing 2"
    - name: my-agent-3
      description: "Does thing 3"
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
---

# My Bundle

@my-bundle:context/instructions.md
@my-bundle:context/philosophy.md
@my-bundle:context/patterns.md
@my-bundle:context/everything-else.md
```

**What's wrong:** Description is too long. Agents are redeclared (behavior handles this). `@main` not pinned. Four context files @mentioned from bundle.md pollute every session.

---

## Context Sink Discipline

Knowledge flows DOWN to where it's used. Root session gets minimal context. Agents @mention what they need.

### Rules

| Rule | Why | How to Check |
|------|-----|--------------|
| Root context ≤ 2 files | More root context = more wasted tokens in every session | Count files in `behavior.context.include` |
| No root file > 100 lines | Long root files = context bloat | `wc -l context/instructions.md context/philosophy.md` |
| Agents @mention only what they need | Focused context = focused output | Review each agent's @mentions |
| No duplicate loading | If behavior includes it, agents don't @mention it again | Cross-reference behavior context.include with agent @mentions |

### What Goes Where

| Content Type | Where It Lives | Loaded When |
|-------------|---------------|-------------|
| Bundle identity + composition | `bundle.md` frontmatter | Always |
| Tool/hook/agent registration | `behaviors/*.yaml` | Always |
| Routing instructions (≤100 lines) | `context/instructions.md` | Always (via behavior) |
| Core principles (≤100 lines) | `context/philosophy.md` | Always (via behavior) |
| Detailed domain knowledge | `context/*.md` (other files) | On-demand (agent @mention) |
| Agent-specific instructions | `agents/*.md` body | When agent is delegated to |
| Mode permissions | `modes/*.md` frontmatter | When mode is activated |

---

## Agent Description Quality (WHY/WHEN/WHAT/HOW)

Every agent's `meta.description` must answer four questions. The LLM reads this to decide whether to delegate — if the description is vague, delegation will be unreliable.

### The Framework

| Question | What It Answers | Example |
|----------|---------------|---------|
| **WHY** | Why does this agent exist? | "Use when improving an existing bundle" |
| **WHEN** | What triggers delegation? | `<example>` blocks showing trigger → delegation |
| **WHAT** | What does it produce? | "Produces a structured findings report" |
| **HOW** | What's the approach? | "Delegates to foundation-expert for structural review" |

### Bad Description

```yaml
meta:
  name: bundle-auditor
  description: "Handles bundle auditing."
```

**Why it's bad:** The LLM doesn't know WHEN to delegate here, WHAT it gets back, or HOW the audit works. It might delegate for the wrong reasons or not at all.

### Good Description

```yaml
meta:
  name: bundle-auditor
  description: |
    Use when improving an existing bundle — performs a full three-level audit.
    Only used in the "improve existing" path. Dispatched by bundle-explorer.

    Reads the entire bundle (bundle.md, behaviors, agents, context, modes, recipes),
    evaluates it against all three convergence levels, and produces a structured
    findings report. Delegates to foundation:foundation-expert for structural/
    philosophical review and amplifier:amplifier-expert for ecosystem positioning.

    Produces: structured findings report (structural issues, philosophical violations,
    capability gaps, evolution recommendations).

    <example>
    Context: Bundle explorer identified this as an "improve" request
    user: "Audit the bundle at ~/dev/my-code-review-bundle"
    assistant: "I'll delegate to bundlewizard:bundle-auditor to perform a full
    three-level audit of your code review bundle."
    </example>
```

### Minimum Standard

Every agent MUST have:
- At least 3 sentences of description (WHY + WHAT + HOW minimum)
- At least 2 `<example>` blocks showing trigger → delegation with `<commentary>`
- A `model_role` that matches the agent's task (coding for generators, critique for reviewers)

---

## Tier Selection Guidance

Use this decision tree to pick the right output tier:

```
Is this adding a capability to an existing bundle?
├── YES → Behavior
│         (YAML + context + maybe agents, composed via includes:)
│
└── NO → Does it need its own bundle.md?
         ├── NO → Behavior (compose it into something bigger)
         │
         └── YES → Does it need modes, recipes, or skills?
                   ├── NO → Bundle
                   │         (standalone with bundle.md, behaviors, agents, context)
                   │
                   └── YES → Application Bundle
                             (full-featured: modes, recipes, skills, possibly modules)
```

**Signs you picked the wrong tier:**
- You're creating modes for a behavior → upgrade to Bundle or Application Bundle
- Your "bundle" has one agent and no modes → downgrade to Behavior
- Your "application bundle" has no recipes or skills → downgrade to Bundle

---

## Common Mistakes with Corrections

| Mistake | Why It's Wrong | Correction |
|---------|---------------|------------|
| Putting agent descriptions in bundle.md | Wastes root context; changes require editing the wrong file | Declare agents in behavior YAML, descriptions in agent .md files |
| @mentioning context from bundle.md body | Loads heavy docs into every session | Move @mentions to agent bodies |
| Declaring same agent in behavior AND bundle.md | Double registration, confusing | Declare in behavior only |
| Using `@main` in published source URIs | Breaking changes hit consumers silently | Pin to version tags (`@v1.0.0`) |
| Creating a "utils" context file | Unfocused grab-bag; every agent loads it "just in case" | Split by topic: one file per concern |
| Agent without examples in description | LLM can't pattern-match when to delegate | Add 2+ `<example>` blocks with `<commentary>` |
| One mega-behavior that does everything | Not reusable; changes affect all consumers | Split by responsibility: one behavior per concern |
| Circular includes (A includes B includes A) | Loader may detect it but don't rely on that | Design acyclic dependency graph |
| Heavy root context (>100 lines) | Context bloat in every session | Shorten root files; move detail to agent @mentions |
| Mode without clear tool permissions | Users don't know what's allowed; agents may bypass intent | Explicit safe/warn/block for every tool |

---

## Expert Delegation Patterns

Bundlewizard agents own the PROCESS. Experts own the KNOWLEDGE. Never guess what an expert would say.

| When You Need | Delegate To | Example Question |
|--------------|-----------|-----------------|
| Composition rule validation | `foundation:foundation-expert` | "Is this includes: structure valid?" |
| URI format verification | `foundation:foundation-expert` | "Is this source URI syntactically correct?" |
| Ecosystem survey | `amplifier:amplifier-expert` | "Does a code review bundle already exist?" |
| Reusable component discovery | `amplifier:amplifier-expert` | "What behaviors should this compose rather than rebuild?" |
| Domain-specific functional testing | Appropriate domain expert | "Does this code review bundle actually review code well?" |

**The delegation discipline:** If you're unsure about a composition rule, delegate. If you're unsure about what exists in the ecosystem, delegate. If you're unsure about domain fitness, delegate. The only thing you should be sure about is the PROCESS.
