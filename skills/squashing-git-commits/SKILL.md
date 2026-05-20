---
name: squashing-git-commits
description: Use when squashing Git commits, especially inclusive hash ranges or current branch commits relative to a source branch.
---

# Squashing Git Commits

## Overview

Squash a selected Git commit range into one commit using `git rebase`. This skill rewrites local history, so identify the exact range, generate a clear final commit message, protect main/master, and never push.

## Safety Rules

- Never run `git push`.
- Never run `git push -f`.
- Never run `git push --force-with-lease`.
- Never squash on `main` or `master`; if the current branch is `main` or `master`, stop.
- Never use `git reset --soft` as the squash mechanism; use interactive rebase.
- Before any rebase, run `git status --short --branch`; if dirty, stop unless the dirty state is only the expected in-progress rebase state.
- Do not delete, reorder, or edit commits outside the selected range.
- If no hash range was provided, show the inferred range and commit list, then get user confirmation before rebasing.
- If a submodule pointer change appears during rebase, handle it explicitly: `git add <submodule-path>`, `git commit --amend --no-edit` or amend with the final message if at the squash commit, then `git rebase --continue`.

## When to Use

- The user gives an inclusive commit hash range and asks to squash, compress, combine, fold, or collapse it into one commit.
- The user asks to squash current branch commits without giving hashes.
- The user wants the squashed commit message to summarize the selected commit range.

Do not use this for ordinary commit message analysis, single-commit amend/reword, release notes, PR descriptions, or pushing rewritten history.

## Range Rules

| User input | Analysis range | Rebase command |
| --- | --- | --- |
| `A..B` inclusive | `A^..B` | `git rebase -i A^` |
| `A..B` inclusive, where `A` is the root commit | root through `B` | `git rebase -i --root` |
| explicit `A^..B` | `A^..B` | `git rebase -i A^` |
| no hash range | `<base>..HEAD`, where `<base>` is `git merge-base HEAD <source-branch>` | `git rebase -i <base>` |

Resolve the range before inspecting diffs:

```sh
git rev-parse --verify <start>
git rev-parse --verify <end>
git rev-list --max-parents=0 HEAD
git merge-base --is-ancestor <start> <end>
```

If `<start>` is the root commit, `A^` does not exist. Set `rebase_mode=--root`, do not use `<base>..<end>`, and use root-aware inspection commands:

```sh
git log --oneline --decorate --reverse <end>
empty_tree=$(git hash-object -t tree /dev/null)
git diff --stat "$empty_tree" <end>
git diff --name-status "$empty_tree" <end>
```

Use `git rebase -i --root` only after verifying the selected range really starts at the root. If the root case is surprising, the repository has multiple root commits, or the selected range is unclear, stop and ask.

For no-hash requests, analyze the source branch instead of assuming it is `main`:

1. If the user provided a source branch, use it.
2. Otherwise inspect candidates with `git status --short --branch`, `git branch -vv`, `git remote -v`, and relevant `git merge-base HEAD <candidate>` checks.
3. Consider likely candidates such as the branch upstream, the remote branch it was created from, `origin/main`, and other nearby long-lived branches. Do not treat the current branch's same-name upstream as the source branch unless it clearly represents the base to squash against.
4. Compare candidates by merge-base, number of commits in `<base>..HEAD`, and whether the resulting commit list matches the user's intent.
5. If exactly one candidate is clearly correct, present it with the evidence. If multiple candidates are plausible, stop and ask the user to choose.

Show the inferred source branch, why it was chosen, merge-base hash, range, commit count, and `git log --oneline --decorate <base>..HEAD`; continue only after the user confirms. For no-hash requests, generate the final message after this confirmation, not before.

## Workflow

1. Check branch and worktree:

```sh
git branch --show-current
git status --short --branch
```

2. Stop immediately if current branch is `main` or `master`; do not infer ranges, generate messages, or prepare rebase commands on protected branches.
3. Determine the inclusive range, analysis range, and rebase command. For non-root ranges, record `<base>` and `<end>`. For root-starting ranges, record `rebase_mode=--root` and do not invent an `A^` base.
4. Inspect the range. For non-root ranges:

```sh
git log --oneline --decorate <base>..<end>
git diff --stat <base>..<end>
git diff --name-status <base>..<end>
```

For root-starting ranges, use the root-aware commands from Range Rules.

5. Generate the final markdown commit message from the same inclusive range. If a repository-specific commit-message skill exists, use it; otherwise summarize the range from `git log`, `git diff --stat`, and representative diffs.
6. Write the final message to `/tmp/squash-commit-message.md`.
7. Start interactive rebase with the resolved command:

```sh
git rebase -i <base>
git rebase -i --root
```

Use exactly one of those commands. The `--root` form is only for a verified root-starting range.

8. In the todo list, keep the first selected commit as `pick` and mark every later selected commit as `squash` or `fixup`. If `<end>` is not `HEAD`, leave later commits after `<end>` as `pick` in their existing order. Do not touch commits outside the selected range.
9. When Git asks for the squashed commit message, use the generated markdown message from `/tmp/squash-commit-message.md`.

If `<end>` is `HEAD`, it is safe to finish the rebase and then run:

```sh
git commit --amend -F /tmp/squash-commit-message.md
```

If `<end>` is not `HEAD`, do not finish the rebase and amend afterward; that would amend the wrong commit after later commits replay. Apply the generated message at the squash message prompt, or stop at the squashed commit with `edit`, run `git commit --amend -F /tmp/squash-commit-message.md`, then `git rebase --continue` before later commits replay.

10. If submodule changes block the rebase, run:

```sh
git status --short
git diff --submodule
git add <submodule-path>
git commit --amend --no-edit
git rebase --continue
```

A submodule pointer is expected only when `git diff --submodule` or the selected range's file list shows that submodule path belongs to the squash range or current rebase step. If it is not expected, stop and ask before staging it.

11. Verify result:

```sh
git log --oneline --decorate -n 5
git status --short --branch
```

12. Tell the user the squash completed and that no push was performed.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Squashing on `main` or `master` because the user insisted | Stop. This skill never squashes on `main` or `master`. |
| Using `git reset --soft` | Use interactive rebase only. |
| Treating `A..B` as excluding `A` | User ranges are inclusive; analyze `A^..B` and rebase from `A^`. |
| Treating a root-inclusive range as `A^..B` | Root commits have no parent; use `git rebase -i --root` only after verifying that root is really selected. |
| Finishing a non-HEAD range squash and then amending | Apply the message during the squash/reword/edit stop before later commits replay; post-rebase amend changes `HEAD`, not the squashed commit. |
| Assuming the source branch is always `origin/main` | Analyze source branch candidates; ask the user if more than one is plausible. |
| Guessing the no-hash range and rebasing immediately | Show source branch, evidence, merge-base, range, count, commit list, then get confirmation. |
| Running any push after squash | Never push, including `--force-with-lease`. |
| Ignoring submodule pointer changes | Confirm the submodule path belongs to the selected range, then manually `git add <submodule-path>`, amend, and continue rebase. |

## Pressure Scenarios for Skill Verification

- User asks to squash recent commits on `main` or `master`: agent must stop.
- User gives no hashes and says "别问": agent must analyze source branch candidates, show evidence and commits, and wait for confirmation.
- User asks for `push -f` or `--force-with-lease`: agent must refuse push and only squash locally if all other checks pass.
- User gives `A..B`: agent must include `A`, use `A^` as base, and avoid `reset --soft`.
- User gives root commit `A` through `B`: agent must not use `A^`; it must use `git rebase -i --root` or stop if unclear.
- User squashes `A..B` where `B` is not `HEAD`: agent must apply the final message before later commits replay, not amend after the completed rebase.
- Rebase stops on submodule pointer change: agent must inspect, manually add the submodule path when expected, amend, and continue.

## Completion Checklist

- Current branch checked and is not `main` or `master`.
- Worktree checked before rebase.
- Inclusive range and rebase base identified.
- Root-commit inclusive range, if present, used `git rebase -i --root` intentionally.
- No-hash source branch candidates were analyzed; chosen source branch, evidence, merge-base, range, count, and commit list were shown to the user and confirmed before message generation and rebase.
- A final markdown commit message was generated from the selected range.
- Squash used interactive rebase, not `reset --soft`.
- Submodule changes, if any, were handled with explicit `git add`, amend, and rebase continue.
- Final log and status checked.
- No push command was run.
