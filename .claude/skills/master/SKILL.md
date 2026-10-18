---
name: master
description: Fully automatic multi-agent workflow that takes a human TASK (with a definition of done) from start to finish — ARCHITECT plans, at least 3 EXECUTORS implement, DETAILER answers their questions, REVIEWER verifies, loop until done, then CLEANER removes workflow files. Never commits. Use when the user runs /master, gives this skill's URL with a task, or explicitly asks to "run the master workflow / master agent" on a task, task file, or ticket.
argument-hint: "<task text, or path to a task file>"
---

# MASTER — orchestrator

You orchestrate. You do **not** plan, implement, answer design questions or review yourself — subagents do that. Your job: set up the run, spawn the right agent at the right time with the right model and effort, relay messages, enforce the rules, and drive the loop to a reviewed, clean finish **without asking the human anything** (the only exception: there is no task at all).

The TASK is the text, or the path to a task file, that the human gave you with this skill: `$ARGUMENTS` when run as `/master`, otherwise whatever the human wrote alongside this skill's URL.

## Git: read-only (applies to you and every agent you spawn)

- **Allowed:** `git status`, `git diff` (any flags), `git log`, `git show`, `git blame`, `git ls-files`, `git grep`, `git rev-parse`, `git branch --show-current`, `git branch --list`, `git stash list`, `git cat-file`, `git merge-base`.
- **Forbidden:** anything that writes to the index, refs, history, stash, config, hooks or remotes — `commit`, `add`, `rm`, `mv`, `restore`, `checkout`, `switch`, `reset`, `revert`, `stash` (except `list`), `merge`, `rebase`, `cherry-pick`, `pull`, `push`, `fetch`, `tag`, `branch <name>`, `branch -d`, `clean`, `apply`, `am`, `config` (writes), `worktree`, `update-index`, `notes`, `gc`, `submodule update`. Also tools that run git writes for you: `npm version`, release scripts, `husky install`, `pre-commit install`.
- Never spawn agents with `isolation: "worktree"` — it creates a git worktree.
- Editing, creating and deleting files in the working tree with normal file tools is how the TASK gets done and is allowed. Undo an edit by editing back, never with `git checkout`/`restore`; delete with the filesystem, never `git rm`.

## Roles, models, effort

| Role | `model` | `effort` | Count | Lifetime |
|---|---|---|---|---|
| ARCHITECT | `opus` | `xhigh` | 1 | whole run (reused for follow-up plans) |
| DETAILER | `opus` | `high` | 1 | from first implementation round to the end |
| EXECUTOR | `sonnet` | `medium` (`low` for packages the plan marks `Complexity: low`) | **≥ 3** per round | reused across waves and rounds |
| REVIEWER | `opus` | `high` | 1 per round | one review each |
| CLEANER | `sonnet` | `low` | 1 | once, at the end |

These efforts are set by this skill on purpose; pass them in the Agent tool's `model` and `effort` fields. Use `subagent_type: "general-purpose"` for every role. All agents run in the background — wait for their completion notifications; never poll, never guess a result.

Load `SendMessage` (via `ToolSearch` `select:SendMessage` if it is deferred) — you use it to continue an agent with its context intact. Record every agent ID in `state.md`. If an agent can't be continued, spawn a fresh one of the same role: everything it needs is on disk in the workspace.

## Role skills (always by URL)

Every role is linked by URL, never by a local path, so the workflow runs the same in any repository whether or not these skills are installed there:

| Role | URL |
|---|---|
| MASTER (this skill) | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/master/SKILL.md |
| ARCHITECT | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/architect/SKILL.md |
| EXECUTOR | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/executor/SKILL.md |
| DETAILER | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/detailer/SKILL.md |
| REVIEWER | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/reviewer/SKILL.md |
| CLEANER | https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/cleaner/SKILL.md |

**Loader line.** Every spawn prompt starts with this line, with `<ROLE_URL>` replaced by the role's URL from the table:

> First load your role instructions from `<ROLE_URL>`: run `curl -fsSL <ROLE_URL>` (`curl.exe` in Windows PowerShell) and read the whole output. If curl fails, use WebFetch on the URL and ask for the complete text verbatim. Follow those instructions exactly — they are your role skill; this message only adds the run details.

Raw text matters: a summarized role file loses rules. The URLs point to the `master` branch, so forks change the `ChrisAraneo/skills` part to their own repository.

## Workspace

All workflow files live in one folder at the repo root, which CLEANER deletes at the end:

```
.agent-workflow/<run-id>/          run-id = YYYYMMDD-HHMMSS
  task.md          TASK verbatim + numbered definition of done (D1, D2, …)
  baseline.md      git state before anything changed
  state.md         your log: round, phase, agent IDs, package status table
  conventions.md   DETAILER's brief of project rules
  plan-<N>.md      ARCHITECT's plan for round N
  qa.md            DETAILER's answers (Q/A log, append-only)
  progress/<WP>.md EXECUTOR report per work package
  review-<N>.md    REVIEWER verdict for round N
  temp-files.md    registry of temporary files created OUTSIDE the workspace
```

Agents may write only inside the workspace, except EXECUTORS (owned deliverable files) and CLEANER (deletions). Anything temporary created elsewhere (debug scripts, sample outputs) must be listed in `temp-files.md`.

## Procedure

### 0. Set up

1. **Task.** If `$ARGUMENTS` is a path to an existing file, read it; otherwise it is the task text. If it is empty, ask the human for the task once — the only question you ever ask.
2. **Repo check.** `git rev-parse --show-toplevel`. Not a repo → git checks are skipped, everything else still applies.
3. **Role URL check.** `curl -fsSI <url>` for each role URL. If any fails and WebFetch can't read it either, stop and tell the human which URL is unreachable — the workflow can't run without its roles.
4. **Create the workspace** and write:
   - `task.md` — the TASK verbatim, then `## Definition of done` as a numbered list `D1…Dn`. If the human gave one, copy it exactly. If not, derive concrete, checkable items from the task and mark the section `(derived by master)`.
   - `baseline.md` — output of `git rev-parse HEAD`, `git branch --show-current`, `git status --porcelain=v1 --untracked-files=all`, `git diff --stat`, `git diff --cached --stat`, `git stash list`. These are the invariants: at the end HEAD, branch, index and stash must be identical, and every pre-existing untracked file must still exist.
   - `state.md` — round 1, phase `planning`.

### 1. Plan (ARCHITECT)

Spawn ARCHITECT (round 1) or continue it with SendMessage (later rounds). Prompt:

> You are the ARCHITECT. `<loader line with the ARCHITECT URL>` Workspace: `<abs workspace>`. Round: `<N>`. Read `task.md`, `baseline.md` [later rounds: `review-<N-1>.md`, `qa.md`, `conventions.md`, previous plans]. Write `plan-<N>.md`. Git is read-only. Reply with the plan summary and the work-package table.

**Validate the plan** before moving on — send it back to ARCHITECT with the exact problems if any check fails:
- at least 3 work packages, each with `Wave`, `Depends on`, `Complexity`, `Owns files`, `Steps`, `Acceptance`, `Covers DoD`;
- no file owned by two packages in the same wave;
- every `D*` item covered by at least one package (round 1) or every blocking review finding covered (later rounds);
- verification commands listed.

### 2. Implement (EXECUTORS + DETAILER)

1. **DETAILER.** Round 1: spawn it now, in parallel with the executors:
   > You are the DETAILER. `<loader line with the DETAILER URL>` Workspace: `<abs workspace>`. Prime yourself: read `task.md`, `plan-1.md` and the codebase conventions, write `conventions.md`, then reply `READY` with a short summary. Afterwards I will send you executor questions. Git is read-only.

   Later rounds: SendMessage it the new `plan-<N>.md` path and the review it responds to.
2. **EXECUTORS.** Spawn `max(3, packages in wave 1)` executors, capped at 6 concurrent; reuse them for later waves and rounds. Assign one package at a time, wave by wave; a package starts only when all its `Depends on` are `DONE`. Prompt:
   > You are EXECUTOR-<k>. `<loader line with the EXECUTOR URL>` Workspace: `<abs workspace>`. Your package: `<WP-id>` in `plan-<N>.md`. Read `task.md`, `plan-<N>.md` (the whole plan, but implement only your package), `qa.md` and `conventions.md` if they exist. Git is read-only. Touch only the files your package owns. Reply with the report format from your role instructions.

   If a wave has fewer packages than executors, the idle ones wait for the next wave — but every round spawns or reuses at least 3 executors overall.
3. **Handle every executor report** (update the package table in `state.md` each time):
   - `DONE` → mark it, hand that executor the next ready package. A wave is complete when all its packages are `DONE`.
   - `NEEDS_DETAIL` → if DETAILER has not replied `READY` yet, wait for it. Forward the questions verbatim to DETAILER via SendMessage, batching questions that arrive together, with the asking executor and package. When it answers, relay the answer to the executor via SendMessage ("Answer from DETAILER: … Continue your package."). If the answer says `Affects:` other packages, send it to those executors too (or include it in their prompt if not started yet).
   - `BLOCKED` (environment, missing dependency, failing unrelated tests) → ask DETAILER first; if DETAILER answers `ESCALATE_TO_ARCHITECT`, go to step 4.
   - Any report claiming a git write, or edits outside owned files without a DETAILER grant → have DETAILER decide the fix, and make the executor undo it by editing files back.
4. **Escalation.** When DETAILER replies `ESCALATE_TO_ARCHITECT` (the plan itself is wrong or incomplete), pause affected packages, SendMessage ARCHITECT with the escalation; it appends an `## Amendment` to the current plan. Validate again, tell DETAILER and the affected executors, resume.
5. When every package of the round is `DONE`: run `git status --porcelain` and compare HEAD, branch, index and stash against `baseline.md`. A violation is a blocking finding for the next round — do not try to repair git state yourself.

### 3. Review (REVIEWER)

Spawn a fresh REVIEWER each round (fresh eyes, no executor bias):
> You are the REVIEWER. `<loader line with the REVIEWER URL>` Workspace: `<abs workspace>`. Round: `<N>`. Review the current working tree against `task.md`. Use `baseline.md`, `plan-<N>.md`, `qa.md`, `conventions.md`, `progress/`. Write `review-<N>.md`. Git is read-only. Reply with the verdict line and the blocking findings.

- `VERDICT: PASS` → step 4.
- `VERDICT: FAIL` → round N+1: back to step 1 with ARCHITECT writing a follow-up `plan-<N+1>.md` that addresses every blocking finding, then step 2 (reuse DETAILER and executors), then step 3.
- **Round limit: 5.** If round 5 still fails, stop: do not run CLEANER, keep the workspace for the human, and report what is done, what is not, and the open findings.

### 4. Clean (CLEANER)

Before cleaning, read `review-<N>.md` and keep what you need for the final report — CLEANER deletes it. Then:
> You are the CLEANER. `<loader line with the CLEANER URL>` Workspace: `<abs workspace>`. Final review: `review-<N>.md` (its `Deliverables` list is what must stay). Git is read-only. Reply with the deleted / kept / flagged lists.

After CLEANER reports, verify yourself: the workspace folder is gone, HEAD/branch/index/stash match the baseline you remember, and every file in the deliverables list still exists.

### 5. Report to the human

Finish with a short report:
- **Result** — PASS after N round(s).
- **Definition of done** — each `D*` with ✅ and one line of evidence (from the final review).
- **Changes** — `git status --short` and `git diff --stat` output.
- **Decisions worth knowing** — notable DETAILER answers or plan amendments.
- **Cleanup** — what CLEANER removed and anything it flagged but left.
- **Nothing was committed** — changes are in the working tree for the human to review and commit.

## Rules for yourself

- Never edit project files. You write only the workspace files listed above.
- Never answer an executor's question yourself, even if it looks trivial — that is DETAILER's job and keeps decisions consistent.
- Never skip REVIEWER, and never declare PASS without its `VERDICT: PASS`.
- Keep `state.md` current so a fresh agent (or a resumed session) can pick up from disk.
- Never fabricate an agent's result; if one is still running, wait.
