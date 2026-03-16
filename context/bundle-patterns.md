# Bundle Construction Patterns

Actionable rules for creating high-quality Amplifier bundles. Referenced by agents that generate, critique, or evaluate bundle artifacts.

## The Thin Bundle Pattern

### bundle.md Rules

1. **≤20 lines YAML frontmatter** — name, version, description, includes. That's it.
2. **NO `@mentions`** in the markdown body — don't pull context files into the root session.
3. **NO redeclaration** — if a behavior provides agents, don't list them again in bundle.md frontmatter.
4. **Includes are composition** — `includes:` says "I am composed of these things." Each included bundle or behavior adds its capabilities.
5. **Markdown body is a menu** — brief description of what's available (modes, agents, recipes). Human-readable orientation, not machine context.

### What Goes Where

| Content Type | Where It Lives | Loaded When |
|-------------|---------------|-------------|
| Bundle identity + composition | `bundle.md` frontmatter | Always (root session) |
| Tool/hook/agent registration | `behaviors/*.yaml` | Always (via includes) |
| Routing instructions | `context/instructions.md` | Always (behavior context.include) |
| Core principles | `context/philosophy.md` | Always (behavior context.include) |
| Detailed domain knowledge | `context/*.md` (other files) | On-demand (agent @mention) |
| Agent instructions | `agents/*.md` body | When agent is delegated to |
| Mode permissions | `modes/*.md` frontmatter | When mode is activated |

## Context Sink Discipline

1. **Root context ≤2 files** — Only `instructions.md` and `philosophy.md` load into every session.
2. **No file >100 lines at root** — If it's longer, it belongs in an agent-level @mention.
3. **Agents @mention only what they need** — `bundle-critic` needs `convergence-criteria.md` and `bundle-patterns.md`. It does NOT need `factory-protocol.md`.
4. **No duplicate loading** — If a behavior includes a context file, agents in that behavior don't @mention the same file again.

## Agent Description Quality (WHY/WHEN/WHAT/HOW)

Every agent's `meta.description` must answer four questions for the LLM that decides whether to delegate:

1. **WHY** does this agent exist? — "Use when [trigger condition]."
2. **WHEN** should it be called? — Examples with `<example>` tags showing trigger → delegation.
3. **WHAT** does it produce? — "Produces [output artifact]."
4. **HOW** does it work? — Brief mention of approach (e.g., "delegates to foundation-expert for structural review").

Bad description: "Handles bundle auditing."
Good description: "Use when improving an existing bundle. Reads the entire bundle, produces a structured findings report covering structural issues, philosophical violations, and capability gaps. Delegates to foundation:foundation-expert for structural review and amplifier:amplifier-expert for ecosystem positioning."

## Composition Hygiene

1. **Source URIs must be pinned** — Use `@v1.0.0` tags, not `@main`, for anything published. During development, `@main` is acceptable with a comment noting it should be pinned before release.
2. **No circular includes** — Bundle A includes B includes A is forbidden. The loader will detect this, but don't rely on the loader.
3. **Behaviors are reusable** — Design behaviors so other bundles could compose them. Don't hardcode bundle-specific paths.
4. **One behavior per concern** — Don't create a mega-behavior that does everything. Split by responsibility.

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|---------------|-----|
| Putting agent descriptions in bundle.md | Wastes root context; changes require editing the wrong file | Put descriptions in agent files; bundle.md just lists names |
| @mentioning context files from bundle.md body | Loads heavy docs into every session | Move @mentions to agent bodies |
| Declaring the same agent in behavior AND bundle.md | Double registration; confusing | Declare in behavior only |
| Using `@main` in published source URIs | Breaking changes hit consumers silently | Pin to version tags |
| Creating a "utils" context file | Unfocused grab-bag; every agent loads it "just in case" | Split by topic |
| Agent without examples in description | LLM can't pattern-match when to delegate | Add 2+ `<example>` blocks |
