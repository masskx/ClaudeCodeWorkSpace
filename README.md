# ClaudeCodeWorkSpace

This repository is the dedicated working directory for Claude Code. Claude Code connects to it through the web version and works inside it. It is a **private workspace** that holds many independent projects. Each project lives in its own folder, and projects must stay isolated from one another.

> **For Claude Code:** read this whole file at the start of every session. The rules below are binding. If a request conflicts with them, say so and ask before proceeding.

## Current status

_Last updated: 2026-10-11_

| Project | Status | Progress | Next step |
|---------|--------|----------|-----------|
| [WeChat Official Account](WeChat%20Official%20Account/README.md) | Active | 16 articles drafted (01–16; article 12 assumes "Jev" = TypeSafe AI's Jev, to be confirmed); 12 earlier topic ideas kept as `.txt` outlines | See below |

**WeChat Official Account** (Chinese-language AI tutorials and research tips for mainland graduate students):

- **Done:** articles 01–16 each have `article.md`, a publishing memo (`发布备忘.md`) and simulated screenshots, except 04. Image/screenshot tooling is in `_工具/`.
- **Image rule:** code-generated images that show a person talking to an Agent must look like the Claude Code desktop client (shared stylesheet `_工具/截图源文件/_agent-ui.css`; rule in the project README). Applied so far to the images in articles 01, 02 and 11 (article 11 is about DeepSeek Harness, so those images are captioned as not its real UI); plain terminal shots are exempt.
- **Topic bank:** `选题库/` holds 20 reserved topics with sources and priorities (`00-选题总表.md`), plus research limits (`调研说明.md`); 5 of them are now written up as articles 06–10.
- **Blocked on you:**
  - Confirm "Jev" means TypeSafe AI's Jev (assumed in article 12); the older "Jev for paper writing" topic is not written separately.
  - Confirm that "Work Body" means Tencent WorkBuddy (assumed in article 04) and that "DeepSeek harness" means DeepSeek Harness `dsh` (assumed in article 11).
- **Still to do by hand:**
  - No article has a cover image yet (`imgs/cover.png`); the prompts are in each memo.
  - Each article has at least one AI-image prompt to generate.
  - Article 04 has 3 screenshot placeholders, and article 14 has 6 (real-use screenshots of WorkBuddy and the Chinese chat apps; I could not fetch them online and did not simulate them).
  - Articles 02–16 describe tools and methods that haven't been tested for real or checked against the original sources; use each memo's "发布前核对" checklist before publishing.

## Repository layout

```
ClaudeCodeWorkSpace/
├── README.md              # This file: workspace-wide rules
├── <project-name>/        # One folder per project
│   ├── README.md          # Required: what it is, how to run it
│   └── ...                # Project's own code, deps, config, tests
└── <another-project>/
```

Only the root `README.md` and shared repo metadata (`.gitignore`, `.github/`) belong at the root. All other work goes inside a project folder.

## Starting a new project

When the work is a standalone project, do these steps in order:

1. **Pick a project name**: lowercase `kebab-case`, short and descriptive (e.g. `price-tracker`, `resume-builder`). Check it doesn't already exist.
2. **Create the folder** at the repo root with that name.
3. **Create `<project-name>/README.md`** before writing any code (see template below).
4. Put everything for the project inside that folder.
5. Add a row for it to the [Project index](#project-index) below.

If the user's request is a change to an existing project, work only inside that project's folder.

## Isolation rules (constraints)

1. **One project, one folder.** Never put project files at the repo root or in another project's folder.
2. **No cross-project imports or references.** Projects must not import code, read files, or depend on paths from sibling projects. If code needs to be shared, ask the user first; the default is to copy it.
3. **Per-project dependencies.** Dependency manifests, lockfiles, virtualenvs, `node_modules`, build output, and configs live inside the project folder. Do not create root-level manifests (`package.json`, `requirements.txt`, etc.).
4. **Stay in scope.** Only modify the project the user asked about. Do not refactor, rename, or "tidy" other projects. Mention problems you notice in other projects instead of fixing them.
5. **Don't touch the root** (including this README's rules) except to update the project index or when the user explicitly asks.
6. **Don't delete or rename a project folder** without explicit confirmation.

## Project README template

Every `<project-name>/README.md` must contain:

```markdown
# <project-name>

One or two sentences: what this project is and why it exists.

## Status
Active | Paused | Done  (plus date last updated)

## Setup
Exact commands to install dependencies.

## Usage
Exact commands to run, test, and build.

## Structure
Brief map of key files and folders.

## Notes
Decisions, known issues, TODOs.
```

Keep it current: update the project README whenever setup, usage, or structure changes.

## Conventions

- **Naming:** folders and files in `kebab-case` unless the language's convention says otherwise (e.g. Python modules use `snake_case`).
- **Language:** documentation in English; code identifiers in English.
- **Tests:** add tests for non-trivial logic and document how to run them in the project README.
- **Secrets:** never commit API keys, tokens, passwords, or `.env` files. Commit a `.env.example` with placeholder values instead. The repo is private, but treat it as if it weren't.
- **Generated files:** keep build output, caches, and large binaries out of git via a `.gitignore` (root-level for common patterns, project-level for project-specific ones).
- **Dependencies:** prefer well-known, maintained packages; pin versions in the project's lockfile.

## Git workflow

- Work on the branch the session designates; never push to another branch without permission.
- Make small, focused commits. Prefix the message with the project name: `price-tracker: add CSV export`.
- A commit should touch **one project only**, apart from the project index update.
- Don't open a pull request unless the user asks for one.
- Don't force-push, rewrite history, or delete branches without explicit approval.

## Working agreement for Claude Code

1. Read this README, then the target project's README, before making changes.
2. For anything ambiguous (project name, scope, tech stack), propose a default and ask briefly rather than guessing on big decisions.
3. Run the project's tests/linters before committing, and report honestly if something fails or was not run.
4. Put scratch or temporary files outside the repo or in git-ignored locations. Do not leave them in project folders.
5. When finished, summarize what changed, in which project folder, and how to run it.

## Project index

| Project | Folder | Description | Status |
|---------|--------|-------------|--------|
| WeChat Official Account | `WeChat Official Account/` | Chinese AI-tutorial and research-tips articles for graduate students (drafts, publishing memos, screenshot tooling) | Active |
