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

Bundle generation and improvement factory. Two paths: create new bundles or improve
existing ones. Default flow is interactive and manual. Autonomous continuation is opt-in
after exploration.

## Modes

| Shortcut | Phase | What Happens |
|----------|-------|--------------|
| `/bundle-explore` | Interview | Understand what you need, route to create or improve — or launch autonomous continuation |
| `/bundle-spec` | Design | Compose the bundle specification |
| `/bundle-plan` | Planning | Break spec into implementation tasks |
| `/bundle-execute` | Generation | Convergence loop: generate → critique → refine → evaluate |
| `/bundle-verify` | Verification | Collect evidence that the bundle works |
| `/bundle-finish` | Delivery | Package, version stamp, deliver |
| `/bundle-debug` | Off-ramp | Diagnose issues at any stage |

## Two Tracks

**Modes are the steering wheel. Recipes are cruise control.**

| Track | How | Best For |
|-------|-----|----------|
| **Interactive** (default) | Navigate modes manually: `/bundle-explore` → `/bundle-spec` → ... | Hands-on sessions, control at each step |
| **Autonomous** (opt-in) | Request autonomy during explore; `bundle-explore` launches the post-explore recipe automatically | End-to-end generation without manual checkpoints |

Both tracks produce the same output. The autonomous track just removes the human
checkpoints after exploration is complete.

## Recipes

| Recipe | Track | What It Does |
|--------|-------|--------------|
| `bundle-autonomous-post-explore.yaml` | Autonomous | Continues after explore: spec → plan → execute → verify → finish. No approval gates. |
| `bundle-development-cycle.yaml` | Interactive | Full pipeline with 3 human approval gates. |
| `bundle-audit.yaml` | Standalone | Audit an existing bundle without full regeneration. |
| `bundle-batch-generation.yaml` | Standalone | Generate multiple bundles from a target list. |

## Getting Started

Say what you want to build, or point me at a bundle to improve. I'll figure out the rest.

To go fully autonomous, add `"go autonomous"`, `"yolo"`, or `"run it all"` to your
request. Exploration still happens first — autonomous continuation begins after.
