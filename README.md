# amplifier-bundle-bundlewizard

An Amplifier bundle that helps users design, create, and scaffold new Amplifier bundles. The bundlewizard guides developers through the complete bundle authoring lifecycle — from intent discovery and design decisions to generating well-structured, production-ready bundle scaffolding.

## What This Bundle Does

- **Guides bundle design** — conversational workflow to capture purpose, agents, behaviors, and context needs
- **Scaffolds bundle structure** — generates the full directory layout, bundle.md, agent descriptions, and context files
- **Validates bundle quality** — checks generated artifacts against Amplifier best practices
- **Documents bundles** — produces README, skill docs, and usage examples

## Structure

```
amplifier-bundle-bundlewizard/
├── agents/               # Agent definitions
├── behaviors/            # Behavior modules
├── context/              # Context files for agents
├── modes/                # Custom modes
├── recipes/              # Multi-step workflows
├── skills/
│   ├── bundle-reference/ # Reference knowledge about Amplifier bundles
│   └── bundle-design/    # Design patterns and best practices
├── templates/            # Bundle scaffolding templates
└── docs/                 # Documentation
```

## Usage

Load this bundle in your Amplifier configuration to get access to the bundlewizard agents and workflows for creating new bundles.

## License

MIT
