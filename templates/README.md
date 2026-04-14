# Starter Templates

Drop-in templates for Cursor-first agent configuration.

## Available Templates

| Template | Target | Size |
|---|---|---|
| [CURSOR-web-app.md](CURSOR-web-app.md) | Web applications (React, Vue, Next.js, etc.) | ~80 lines |
| [CURSOR-ml-project.md](CURSOR-ml-project.md) | ML/AI projects (training, inference, data pipelines) | ~80 lines |
| [CURSOR-library.md](CURSOR-library.md) | Libraries and packages (npm, PyPI, crates.io) | ~70 lines |
| [REVIEW.md](REVIEW.md) | Code review guidelines (any project type) | ~60 lines |
| [session-handoff.md](session-handoff.md) | End-of-session continuity handoff template | ~20 lines |
| [structured-reasoning.md](structured-reasoning.md) | Premises/trace/conclusions/rejected-paths template | ~20 lines |
| [chronicle.md](chronicle.md) | Strategic project timeline template for long-running efforts | ~25 lines |
| [memory-project.md](memory-project.md) | Project memory template with goals, decisions, and constraints | ~35 lines |
| [memory-reference.md](memory-reference.md) | Reference memory template for stable facts and lookups | ~30 lines |

## How to Use

1. Copy the relevant template to your project root.
2. Keep the file name as-is or rename to your local policy file.
3. Fill in project-specific values (marked with `{{placeholder}}`).
4. Remove sections that don't apply.
5. Add project-specific deterministic checks.

## Design Principles

- **Under 150 lines** - fits in a single KV-cache prefix for efficiency
- **Commands before prose** - `npm test`, `cargo build` before explanations
- **Code over descriptions** - style shown by example, not described in words
- **No linting rules** - use deterministic tools (eslint, ruff) instead
- **No general programming advice** - only project-specific, non-obvious rules
