# Bundlewizard Upgrade Design

## Goal

Add durable, version-aware upgrade metadata to every generated bundle and route upgrade intent — both explicit and automatically detected — through a contained specialization of the existing `improve_existing` flow.

## Background

Bundlewizard generates bundle repos like `~/dev/amplifier-bundle-project-memory`. Those repos carry a provenance block stamped at packaging time, but the current legacy shape is too sparse to support a real upgrade path:

```yaml
bundle:
  bundlewizard:
    packaged_at: 2026-03-17T11:24:43Z
    level_score: 0.94
    critic_verdict: PASS
    tests_passed: 223
    tests_failed: 0
    commits: 7
```

This shape lacks:
- The Bundlewizard generator version that produced it
- A schema version that upgrade logic could key off
- Any signal that tells a future Bundlewizard run what migration steps apply

At the same time, Bundlewizard's own stamping behavior has no single authoritative source: its real bundle version lives in `bundle.md`, but the stamping instructions are a duplicated literal in `agents/bundle-packager.md`.

The result is that when a user or an autonomous run targets an older generated repo with "upgrade," Bundlewizard falls through to the generic `improve_existing` path with no awareness that a metadata migration is also needed. There is no version contract, no migration rule, and no reliable upgrade surface.

## Chosen Approach

Three approaches were considered:

1. **Separate upgrade track** — a new mode stack, recipe, and routing surface dedicated to upgrade. Rejected: duplicates the existing improve machinery, creates a second parallel flow, adds unnecessary surface area.

2. **Silent auto-migration only** — detect old provenance and normalize it silently inside the improve path, with no explicit upgrade concept. Rejected: too hidden, not testable as a first-class feature, weak fit for the explicit upgrade requirement.

3. **Hybrid routed upgrade inside the existing flow** — upgrade becomes a routed specialization of `improve_existing`, triggered by either explicit user intent or automatic legacy detection. **This is the approved approach.**

The work is staged in two phases:

- **Phase B** — add a durable canonical provenance block and upgrade stub (the metadata contract that makes C safe)
- **Phase C** — add real routing, detection, and execution logic that reads the Phase B contract

## Architecture

```
User/Caller intent
       │
       ▼
bundle-explore
  ├── explicit upgrade intent detected?
  │        (upgrade / refresh / migrate / bring up to date)
  │
  └── automatic legacy detection?
           ├── bundle.bundlewizard present → legacy shape
           ├── generated_by present but no schema_version → old shape
           └── generated_by.schema_version < current → stale shape
                    │
                    ▼
             improve_existing path
             + upgrade-specific handoff fields
                    │
                    ▼
             bundle-spec / bundle-plan / bundle-execute
                    │
                    ▼
             bundle-packager
             (normalizes provenance, writes canonical generated_by)
```

No new mode stack. No new autonomous universe. The upgrade path is a self-contained routing branch inside `bundle-explore`, and all packaging writes back through the single existing packager.

## Components

### Canonical Provenance Block

Every newly generated or upgraded bundle will carry this normalized block in `bundle.md`:

```yaml
bundle:
  name: <bundle-name>
  version: <bundle-version>
  generated_by:
    tool: bundlewizard
    version: <bundlewizard-version>          # sourced from bundlewizard's own bundle.md
    schema_version: 1                         # integer, keyed by upgrade logic
    timestamp: <iso8601>
    mode: interactive | autonomous
    convergence:
      level_score: <float>
      critic_verdict: PASS | FAIL
      tests_passed: <int>
      tests_failed: <int>
      commits: <int>
```

**The upgrade stub** is specifically the four fields that upgrade logic reads first:

- `generated_by.tool`
- `generated_by.version`
- `generated_by.schema_version`
- `generated_by.timestamp`

Everything under `convergence` is audit trail and does not gate upgrade routing.

### Legacy Fingerprint

The following patterns identify an older generated repo that needs migration:

| Pattern | Classification |
|---|---|
| `bundle.bundlewizard` present, no `generated_by` | Legacy (pre-schema) |
| `generated_by` present, no `schema_version` | Old (schema unversioned) |
| `generated_by.schema_version < current` | Stale (upgradeable) |
| No recognizable provenance at all | Unknown origin |

### Version Source

Bundlewizard must stamp its own version from a single authoritative source — its actual bundle version at `bundle.md` — not from a duplicated hardcoded literal in packager instructions. The fix in Phase B establishes this as the only source of truth.

### Upgrade-Aware Handoff Fields

After `bundle-explore` routes into upgrade behavior, the handoff payload should include upgrade-specific fields alongside the existing `improve_existing` fields:

```yaml
path_decision: improve_existing
upgrade_requested: true
upgrade_reason: explicit_intent | legacy_provenance_detected | schema_mismatch
provenance_shape: legacy_bundlewizard | generated_by_v1 | none
source_schema_version: 0 | 1 | unknown
target_schema_version: 1
```

## Data Flow

1. **Audit** — `bundle-explore` inspects the target bundle's provenance block to classify its state (see Upgrade State Model)
2. **Route** — if upgrade conditions are met, upgrade-specific handoff fields are added
3. **Normalize provenance first** — `bundle-packager` migrates `bundle.bundlewizard` → `bundle.generated_by`, adds `version`, adds `schema_version`
4. **Continue improve pipeline** — spec, plan, execute proceed normally; if only metadata migration was needed the plan is minimal
5. **Package with canonical shape** — final packaging always writes the canonical `generated_by` block; the legacy `bundle.bundlewizard` block is removed; no dual-write

## Upgrade State Model

| State | Condition | Action |
|---|---|---|
| **Legacy-generated** | `bundle.bundlewizard` present, no `generated_by` | Migrate provenance first, then upgrade flow |
| **Generated, current schema** | `generated_by.schema_version == current` | No schema migration; proceed only if explicit upgrade intent requests substantive improvement |
| **Generated, older schema** | `generated_by.schema_version < current` | Run schema migration, then upgrade flow |
| **Unknown origin** | No recognizable bundlewizard provenance | Stay in normal `improve_existing` unless caller explicitly requests forced upgrade |

## Error Handling

### Hard-stop / takeover conditions

Pause and write takeover guidance to `STATE.yaml` (reusing the same pattern from the post-explore autonomy design) when:

- `bundle.md` cannot be parsed
- Provenance block is structurally contradictory (e.g., both legacy and new shapes present with conflicting values)
- Target repo is missing required surface files needed for a safe upgrade
- Migration would overwrite metadata that appears to be user-authored rather than generated
- Bundle has no recognizable bundlewizard origin and the caller did not explicitly request a forced upgrade path

`STATE.yaml` takeover fields for upgrade failures follow the established pattern: recommended re-entry point, explanation, and caller notes.

### Soft auto-proceed conditions

Continue without human intervention when:

- Provenance is clearly old but unambiguously recognizable (legacy fingerprint matches)
- All missing fields can be derived without guesswork (`version` from bundlewizard's own metadata, `schema_version` from current target)
- No user-authored metadata is at risk of being overwritten

### Migration preservation rule

When normalizing legacy provenance, existing audit values (`packaged_at` → `timestamp`, `level_score`, `critic_verdict`, `tests_passed`, `tests_failed`, `commits`) are preserved in `convergence`. Nothing is silently discarded.

## Testing Strategy

### Layer 1 — Metadata migration fixture tests

Use `~/dev/amplifier-bundle-project-memory`'s actual `bundle.md` provenance shape as the canonical reference fixture for the old format.

Tests to cover:

- Legacy shape is correctly detected (`bundle.bundlewizard` fingerprint)
- Migration produces the canonical `generated_by` block
- `generated_by.version` is present and matches the authoritative bundlewizard version source
- `generated_by.schema_version` is stamped as `1`
- Existing audit values (`level_score`, `critic_verdict`, etc.) are preserved in `convergence`
- Legacy `bundle.bundlewizard` block is removed after migration
- Running the migration a second time on an already-migrated bundle is idempotent (no duplicate fields, no version drift)

### Layer 2 — End-to-end upgrade validation

Using `~/dev/amplifier-bundle-project-memory` as the live target:

- Seed or preserve the old provenance shape in the target repo
- Run the upgrade path (both via explicit intent trigger and automatic detection trigger)
- Verify migrated metadata matches canonical shape
- Verify the resulting bundle repo is in a valid final state

## File Touch Map

### Phase B — Durable metadata / upgrade stub

| File | Change |
|---|---|
| `agents/bundle-packager.md` | Normalize canonical output to `bundle.generated_by`; stamp tool/version/schema_version/timestamp/mode/convergence; source generator version from bundlewizard's real version source; add migration behavior for legacy `bundle.bundlewizard` shape |
| `context/factory-protocol.md` | Define the canonical generated-bundle provenance schema; define `generated_by.version` and `generated_by.schema_version`; define legacy-shape recognition rules |
| `context/autonomous-protocol.md` | Align autonomous packaging audit policy with the canonical provenance shape; ensure autonomous runs write upgrade-capable metadata |
| `tests/` | Fixture for the old project-memory provenance shape; tests for detection, migration, schema stamping, audit value preservation, legacy block removal, and idempotency |

### Phase C — Routed upgrade behavior

| File | Change |
|---|---|
| `modes/bundle-explore.md` | Detect explicit upgrade intent (upgrade/refresh/migrate/bring up to date); detect legacy/old-schema provenance automatically; route upgrade as a specialization of `improve_existing`; populate upgrade-aware handoff fields |
| `context/instructions.md` | Expose "upgrade existing generated bundle" as a real supported user-facing concept; clarify that upgrade uses the existing improve flow, not a separate track |
| `bundle.md` | Bump bundle version to reflect this new capability |
| `recipes/bundle-autonomous-post-explore.yaml` | Ensure the autonomous post-explore recipe handles upgrade-aware handoff fields when they are present |
| `tests/test_modes_adherence.py` | Add routing surface checks for upgrade intent detection and auto-detection of legacy provenance |

### Live validation target (read-only reference, not modified in-repo)

- `~/dev/amplifier-bundle-project-memory` — used as a real-world old-format bundle to validate detection and migration behavior end-to-end

## Implementation Order

1. **Canonical metadata contract** — define the `generated_by` schema and legacy fingerprint in `context/factory-protocol.md`; this is the source of truth all subsequent changes key off
2. **Packager stamping + legacy migration** — update `agents/bundle-packager.md` to write canonical provenance and migrate old shape; align `context/autonomous-protocol.md`
3. **Fixture + metadata migration tests** — add the old-format fixture and Layer 1 tests before any routing work lands
4. **Explore routing** — add explicit and automatic upgrade detection in `modes/bundle-explore.md` with upgrade-aware handoff fields
5. **Public surface + docs** — update `context/instructions.md`, bump `bundle.md` version, align `recipes/bundle-autonomous-post-explore.yaml`
6. **End-to-end validation** — run Layer 2 tests against `~/dev/amplifier-bundle-project-memory`; verify the full round-trip

## Open Questions

None. All design decisions were resolved during the approved design session:
- Upgrade UX: explicit intent + auto-detection (Option C)
- Routing model: hybrid, inside existing improve flow (Approach 3)
- Version source: bundlewizard's own `bundle.md`, not duplicated literals
- Error model: hard-stop to `STATE.yaml` for ambiguous cases, soft auto-proceed for recognizable legacy shapes

## Success Criteria

- `~/dev/amplifier-bundle-project-memory`'s legacy `bundle.bundlewizard` shape is recognized without manual hints
- Provenance is rewritten to canonical `bundle.generated_by` with all required fields
- Stamped `generated_by.version` matches the authoritative Bundlewizard version source
- `generated_by.schema_version` is present and set to `1`
- Re-running upgrade on an already-migrated bundle produces no changes (idempotent)
- Upgraded repo passes all existing bundle validation checks
- Explicit upgrade intent phrases route correctly without triggering the normal improve flow prematurely
- Automatic legacy detection routes without any user intervention
