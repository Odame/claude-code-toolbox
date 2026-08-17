# CLAUDE.md

## Overview

Personal collection of Claude Code plugins, skills, and hooks, published as a plugin marketplace.

## Repository layout

Each plugin lives in `plugins/<name>/`, registered in the root `.claude-plugin/marketplace.json`. A plugin's hooks invoke its command-line script as `uv run --project "${CLAUDE_PLUGIN_ROOT}" <script> <subcommand>`.

## Commands

Run from repo root, using the `uv` workspace:

- Install/sync all plugin packages: `uv sync --all-packages`
- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Test one plugin: `uv run pytest plugins/<name>`
- Test a single test: `uv run pytest plugins/<name>/tests/test_file.py::test_name`

## Adding a plugin

1. Create `plugins/<name>/`, following an existing plugin (e.g. `plugins/plain-english-checker`) for layout.
2. Register it in the root `.claude-plugin/marketplace.json`.
3. Give it its own `pyproject.toml` (hatchling backend, `dev` group with `pytest` + `ruff`).
4. Before considering it done: `uv sync`, `pytest` passes, `ruff check` and `ruff format --check` pass clean, and `git status` shows nothing gitignore-worthy staged.

## Commits

Use Conventional Commits (`type(scope): description`).

## Writing skills and agent docs

Use the `/writing-for-agents` skill for any document written for an agent to read: `SKILL.md`, `CLAUDE.md`, `AGENTS.md`, and the like.

## Agent skills

### Issue tracker

GitHub Issues (Odame/claude-code-toolbox), via `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.
