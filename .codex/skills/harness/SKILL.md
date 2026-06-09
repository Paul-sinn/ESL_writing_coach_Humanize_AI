---
name: harness
description: Use when creating, reviewing, or executing Codex Harness phase plans for this project. Reads .codex/commands/harness.md plus harness/harness-framework-codex AGENTS/docs, then creates phases/index.json, phases/<phase>/index.json, and self-contained stepN.md files with executable acceptance criteria.
---

# Harness

Use this skill for `$harness`, “phase 만들기”, or any Codex Harness workflow in this repository.

## Required sources

Read these before designing phases:

1. `.codex/commands/harness.md` — single source of truth for Harness workflow and file formats.
2. `harness/harness-framework-codex/AGENTS.md` — project/process guardrails.
3. `harness/harness-framework-codex/docs/PRD.md` — product intent.
4. `harness/harness-framework-codex/docs/ARCHITECTURE.md` — repo structure and validation surfaces.
5. `harness/harness-framework-codex/docs/ADR.md` — technical decisions.
6. `harness/harness-framework-codex/docs/UI_GUIDE.md` — read only for frontend/UI phases.

Never create or reference `CLAUDE.md` or `.claude/`. Never access `.env`.

## Phase creation workflow

1. Pick a kebab-case phase directory name. If the user did not provide one, infer the smallest useful phase from the current task and state that assumption.
2. Create/update `phases/index.json` with `{ "dir": "<phase>", "status": "pending" }` without timestamps.
3. Create `phases/<phase>/index.json`:
   - `project`: use `ESL Academic Writing Coach` unless project docs specify another name.
   - `phase`: same as directory name.
   - `steps`: zero-based, kebab-case names, all `pending`.
4. Create one `stepN.md` per step. Each step must be self-contained for a fresh Codex session.
5. Keep each step narrow: one layer/module per step. Include concrete file paths, expected signatures or contracts, executable AC commands, and explicit “do not” rules.
6. Do not run the Harness executor unless the user explicitly asks to execute the phase.

## Step template requirements

Each `stepN.md` must include:

- `# Step N: <name>`
- `## 읽어야 할 파일` with the harness docs plus relevant repo files.
- `## 작업` with specific implementation instructions and boundaries.
- `## Acceptance Criteria` containing runnable shell commands.
- `## 검증 절차` including status update rules for `phases/<phase>/index.json`.
- `## 금지사항` with concrete “X를 하지 마라. 이유: Y” items.

For this project, prefer verification commands that avoid `.env` when possible, e.g. `python -m py_compile ...`, targeted frontend commands from `frontend/`, or tests only when they will not violate local instructions.
