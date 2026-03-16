---
mode:
  name: bundle-finish
  description: Package the bundle — version stamp, git init, deliver
  shortcut: bundle-finish

  tools:
    safe:
      - read_file
      - glob
      - grep
      - write_file
      - edit_file
      - bash
      - delegate
      - load_skill

  default_action: block
  allowed_transitions: []
  allow_clear: true
---

BUNDLE-FINISH MODE: Package and deliver the generated bundle.

This is the terminal mode. No further transitions — the pipeline is complete.

Delegate to `bundlewizard:bundle-packager` for packaging.

## Delivery Options

Present these options to the user:

| Option | What Happens |
|--------|-------------|
| **merge** | Merge changes into the target branch (for improve path) |
| **pr** | Create a pull request with the changes (for improve path) |
| **keep** | Keep the generated bundle in its output directory (for create new) |
| **discard** | Delete the generated artifacts (rare — usually means starting over) |

For "create new" path: the packager runs `git init`, creates the first commit, and optionally pushes to a GitHub repo.

For "improve existing" path: the packager creates a feature branch with the changes and offers merge or PR.

## Version Stamp

The packager adds convergence metadata to the generated bundle's frontmatter. This is non-negotiable — every machine-generated bundle must be traceable.

## Completion

When delivery is complete, clear the mode:
`mode(operation='clear')`
Do NOT leave the mode active after the pipeline is finished.
