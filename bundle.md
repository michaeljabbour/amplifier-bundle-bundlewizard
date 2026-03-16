---
bundle:
  name: bundlewizard
  version: 0.1.0
  description: |
    Bundle generation and improvement factory for the Amplifier ecosystem.
    Generates new bundles and improves existing ones through structured
    interview + iterative convergence using the factory pattern.

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: bundlewizard:behaviors/bundlewizard
---

# Bundlewizard

Bundle generation and improvement factory. Two paths: create new bundles or improve existing ones.

## Modes

| Shortcut | Phase | What Happens |
|----------|-------|--------------|
| `/bundle-explore` | Interview | Understand what you need, route to create or improve |
| `/bundle-spec` | Design | Compose the bundle specification |
| `/bundle-plan` | Planning | Break spec into implementation tasks |
| `/bundle-execute` | Generation | Convergence loop: generate → critique → refine → evaluate |
| `/bundle-verify` | Verification | Collect evidence that the bundle works |
| `/bundle-finish` | Delivery | Package, version stamp, deliver |
| `/bundle-debug` | Off-ramp | Diagnose issues at any stage |

## Recipes

- `bundle-development-cycle.yaml` — Full pipeline with approval gates
- `bundle-audit.yaml` — Standalone audit for existing bundles
- `bundle-batch-generation.yaml` — Generate multiple bundles from a target list

## Getting Started

Say what you want to build, or point me at a bundle to improve. I'll figure out the rest.
