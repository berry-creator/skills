---
name: rebasing-branch-onto-target
description: Use when rebasing the current Git branch onto a target branch or commit, especially when the target may need to be inferred or the branch may need cleanup before rebasing.
---

# Rebasing Branch Onto Target

## Overview

Rebase the current branch onto a target branch or commit using ordinary `git rebase <target>`. This skill rewrites local history but should preserve final content, so it protects `main` and `master`, checks remote freshness when relevant, records the original branch head, never pushes, and pauses when the branch should likely be cleaned up before rebasing.

**REQUIRED SUB-SKILLS:**

- Use `refactoring-branch-commits` if the current branch should be reordered before rebasing.
- Use `squashing-git-commits` if the current branch should be squashed before rebasing.

## Safety Rules

- Never run `git push`.
- Never run `git push -f`.
- Never run `git push --force-with-lease`.
- Never rebase `main` or `master`; if the current branch is `main` or `master`, stop.
- Before any rebase, run `git status --short --branch`; if dirty, stop unless the dirty state is only the expected in-progress rebase state.
- Use this skill only for ordinary `git rebase <target>`. Do not use `git rebase --onto` here.
- The source branch is the current branch unless the user explicitly says otherwise.
- Do not rebase a branch onto itself. If the target branch is the current branch, stop.
- Do not rebase onto the current `HEAD` commit. If the target commit equals `HEAD`, stop.
- If the current branch has an upstream or source analysis depends on remote refs, fetch that upstream ref before rebasing.
- If the target branch is a local branch with an upstream, or target analysis depends on remote refs, fetch that target upstream ref before rebasing.
- If the current branch and its remote-tracking branch differ, stop and ask whether the user wants `git pull --rebase` first.
- If the target branch and its remote-tracking branch differ, stop and ask whether the user wants to update that target branch with `git pull --rebase` first before using it as the rebase base.
- If no target branch or commit was provided, analyze candidates, show the evidence, and get user confirmation before rebasing.
- Before rewriting history, record the original `HEAD` SHA for final verification.
- If the current branch contains multiple commits relative to the target, show the commit count and list, then ask whether the user wants to continue rebasing as-is, refactor commits first, or squash first.
- If rebase conflicts occur, resolve them by semantic ownership of each changed block. Do not choose wholesale `ours` or `theirs` unless the whole file truly belongs to one side.
- If a conflict cannot be resolved confidently from the original diffs and target state, stop after presenting the conflict state.
- If a submodule pointer change appears during rebase, handle it explicitly: `git add <submodule-path>`, `git rebase --continue`, and stop if the pointer change was not expected from the rebased commits.

## When to Use

- The user asks to rebase the current branch onto a named branch.
- The user asks to rebase the current branch onto a specific commit SHA.
- The user asks to make the current branch based on another branch or commit.
- The user asks to "rebase onto", "move onto", "replay onto", or "rebase this branch on top of" a target.

Do not use this for interactive reordering, multi-group squash planning, `git rebase --onto`, merge/integration workflows, or push requests.

## Target Analysis

Treat the target as one of two kinds:

| Target kind | Verification | Rebase command |
| --- | --- | --- |
| branch or remote-tracking ref | Verify the exact ref the user named, refresh remote when relevant | `git rebase <branch-or-ref>` |
| commit | Verify exact commit exists | `git rebase <commit>` |

If the user did not provide a target:

1. Inspect branch context:

```sh
git status --short --branch
git branch -vv
git remote -v
git branch --all
```

2. Consider likely targets such as explicit upstream, the branch the current branch was created from, `origin/main`, `origin/master`, `main`, `master`, release branches, and other nearby long-lived branches.
3. Compare candidates with:

```sh
git merge-base HEAD <candidate>
git log --oneline --decorate <candidate>..HEAD
git log --oneline --decorate HEAD..<candidate>
```

4. Present the inferred target, evidence, source branch, merge-base, commit count, and commit list.
5. Continue only after the user confirms. If multiple candidates are plausible, ask the user to choose.

If the user provided a local branch name, verify that exact local branch:

```sh
git rev-parse --verify <branch>
```

If the user provided a remote-tracking ref such as `origin/main`, verify that exact ref:

```sh
git rev-parse --verify <remote-tracking-ref>
```

For current-branch freshness, if the current branch has an upstream or source freshness depends on remote refs, resolve the exact upstream ref and refresh it:

```sh
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git fetch <upstream-remote> <upstream-branch>
git rev-parse HEAD
git rev-parse @{upstream}
git merge-base --is-ancestor HEAD @{upstream}
git merge-base --is-ancestor @{upstream} HEAD
```

If there is no upstream and no explicit remote source ref, state that source sync is local-only. If local source and upstream differ, stop and ask whether the user wants `git pull --rebase` first.

For target freshness, if the target is a local branch with an upstream or target freshness depends on remote refs, resolve the exact target upstream ref and refresh it:

```sh
git rev-parse --abbrev-ref --symbolic-full-name <target>@{upstream}
git fetch <target-upstream-remote> <target-upstream-branch>
git rev-parse <target>
git rev-parse <target>@{upstream}
git merge-base --is-ancestor <target> <target>@{upstream}
git merge-base --is-ancestor <target>@{upstream} <target>
```

If the user clearly means the remote-tracking target, fetch and verify that exact ref directly, then rebase onto that exact ref. Do not silently swap local and remote target refs. If a local target branch has no upstream and no explicit remote target ref, state that target sync is local-only. If local target and upstream differ, stop and ask whether the user wants to update that target branch with `git pull --rebase` first.

If the user provided a commit SHA, verify it exactly:

```sh
git rev-parse --verify <commit>^{commit}
```

Do not reinterpret a verified commit as a branch target unless the user asks.

## Multi-Commit Decision Point

Before rebasing, inspect how many commits the current branch has relative to the target:

```sh
git merge-base HEAD <target>
git merge-base --is-ancestor HEAD <target>
git merge-base --is-ancestor <target> HEAD
git rev-list --count <target>..HEAD
git log --oneline --decorate <target>..HEAD
```

Interpret the result in this order:

- If `HEAD` is already an ancestor of the target, stop and explain the current branch is already contained in the target; ordinary rebase is unnecessary and the user may actually want merge, reset, or branch switching.
- If the target is an ancestor of `HEAD`, the branch is ahead of the target by the listed commits.
- If neither side is an ancestor of the other, the branch and target have diverged; the listed commits are the branch-only commits that ordinary rebase would replay.

Then apply the decision point:

- `0` branch-only commits: stop and explain there is nothing to replay onto the target.
- `1` branch-only commit: continue normally unless the user wants to edit that single commit first.
- Greater than `1` branch-only commits: show the count and commit list, then ask whether to continue as-is, use `refactoring-branch-commits`, or use `squashing-git-commits`.

Do not silently refactor or squash. The user must choose.

## Content Preservation

Ordinary rebasing should preserve the branch's final content unless the user explicitly asked for content changes. Before rebasing, record the original branch head:

```sh
git rev-parse HEAD
```

After the rebase, verify the final tree still matches the recorded original head when the goal was history-only rewriting:

```sh
git diff --exit-code <original-head> HEAD
```

Commit hashes are expected to change. A non-empty final diff means the rebase changed content and must be explained, corrected, or explicitly approved by the user.

## Conflict Resolution During Rebase

When conflicts occur, resolve each conflicted block by asking which original commit introduced or intentionally changed that content. Use the rebased commit list, changed paths, and representative diffs as evidence:

```sh
git show --name-status --format=fuller <selected-commit>
git show --format=fuller --find-renames <selected-commit> -- <path>
git diff <target>..<original-head> -- <path>
```

Rules:

- Preserve the branch's intended final content unless the user explicitly asked to change it.
- Preserve the target branch or target commit state below the rebased commit stack; rebase should replay branch commits on top of that target, not rewrite the target.
- Avoid file-wide `ours` or `theirs`; it can silently discard blocks from either the target or the rebased commits.
- After resolving a conflicted file, compare it against the original final branch version for that path when the goal is content preservation:

```sh
git diff <original-head> -- <path>
```

If that path-level diff is non-empty, explain why it is expected or correct it before continuing.

## Workflow

1. Check branch and worktree:

```sh
git branch --show-current
git status --short --branch
git branch -vv
```

2. Stop immediately if the current branch is `main` or `master`.
3. Determine the target branch or commit. Stop if the target is the current branch or current `HEAD`. If inferred, show the evidence and get confirmation.
4. Refresh current-branch upstream when relevant. If local source and upstream differ, stop and ask whether the user wants `git pull --rebase` first. If there is no upstream and no explicit remote source ref, state that source sync is local-only.
5. Refresh target upstream when relevant. If local target and upstream differ, stop and ask whether the user wants to update that target branch with `git pull --rebase` first. If the user intended the remote-tracking ref, fetch and rebase onto that exact ref. If there is no target upstream and no explicit remote target ref, state that target sync is local-only.
6. Record the original `HEAD` SHA for final tree verification:

```sh
git rev-parse HEAD
```

7. Inspect branch/target ancestry and how many branch-only commits would be replayed:

```sh
git merge-base HEAD <target>
git merge-base --is-ancestor HEAD <target>
git merge-base --is-ancestor <target> HEAD
git rev-list --count <target>..HEAD
git log --oneline --decorate <target>..HEAD
```

8. If `HEAD` is already contained in the target, stop. If there are multiple branch-only commits, ask whether to continue as-is, refactor first, or squash first. If the user chooses refactor or squash, stop this workflow and use the required sub-skill.
9. Start the ordinary rebase onto the exact confirmed target ref or commit:

```sh
git rebase <target>
```

10. If submodule changes block the rebase, inspect them before staging:

```sh
git status --short
git diff --submodule
git add <submodule-path>
git rebase --continue
```

Only stage the submodule path when the pointer change is expected from the rebased commits or current rebase step. Otherwise stop and ask.

11. Verify result:

```sh
git status --short --branch
git log --oneline --decorate -n 10
git diff --exit-code <original-head> HEAD
```

`range-diff` is also useful to inspect how the old commits mapped onto the rebased history:

```sh
git range-diff <target>..<original-head> <target>..HEAD
```

12. If a repository-specific validation command exists, run it after tree equality is confirmed.
13. Tell the user the rebase completed, whether final content matched the original head, whether multi-commit cleanup or remote-sync decisions were needed, and that no push was performed.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Using this skill for `git rebase --onto` | Stop and use a different workflow; this skill only covers ordinary `git rebase <target>`. |
| Rebasing `main` or `master` because the user asked | Stop. This skill never rebases protected branches. |
| Rebasing a branch onto itself or onto current `HEAD` | Stop; there is no meaningful ordinary rebase to perform. |
| Guessing the target and rebasing immediately | Show target evidence, merge-base, commit count, and commit list, then get confirmation. |
| Rebasing while the current branch is stale relative to its upstream | Resolve and fetch the exact upstream ref first; if local and upstream differ, ask whether to run `git pull --rebase` first. |
| Rebasing onto a stale local target branch | Resolve and fetch the exact target upstream ref first; if local and upstream differ, ask whether to update that target branch with `git pull --rebase` first. |
| Treating `0` commits in `<target>..HEAD` as always meaning "already based on target" | Check ancestry first; `HEAD` may already be contained in the target instead of ahead of it. |
| Rebasing a multi-commit branch without checking whether cleanup is needed | Show the commit count and list, then ask whether to continue, refactor, or squash first. |
| Defaulting no-target requests to `origin/main` | Analyze target candidates and ask if more than one is plausible. |
| Treating a commit target like a branch target | Verify the commit SHA exactly and use it as-is. |
| Silently rebasing onto local `<target>` when the user meant `origin/<target>` | Confirm the exact ref and rebase onto that exact ref. |
| Resolving conflicts with wholesale `ours` or `theirs` | Resolve by semantic ownership of changed blocks and verify conflicted paths against the original final tree. |
| Treating changed commit hashes as a verification failure | Hashes change after rebase; verify final tree equality with `git diff --exit-code <original-head> HEAD`. |
| Pushing after rebase | Never push, including force push. |

## Pressure Scenarios for Skill Verification

- User asks to rebase current branch onto `main` while already on `main`, or onto the current branch or current `HEAD`: agent must stop.
- User omits the target or says "rebase onto whatever this branch came from": agent must analyze target candidates, show evidence, and wait for confirmation.
- User provides a commit SHA target: agent must verify the commit and use ordinary `git rebase <commit>`.
- Current branch has no upstream: agent must state that source sync is local-only instead of inventing `origin/<branch>`.
- Current branch is behind or diverged from its upstream: agent must fetch, detect the mismatch, and ask whether the user wants `git pull --rebase` first.
- Target local branch has no upstream: agent must state that target sync is local-only unless the user explicitly asked for a remote-tracking ref.
- Target branch is behind or diverged from its remote-tracking branch: agent must fetch, detect the mismatch, and ask whether the user wants to update that target branch with `git pull --rebase` first.
- `origin/main` already contains the current branch head, or the branch has `0` replayable commits: agent must stop and explain that ordinary rebase is unnecessary.
- Current branch has multiple commits relative to target: agent must show the count and commit list, then ask whether to continue, refactor, or squash first.
- User says "just do it, don't ask" for an inferred target, or asks for `git rebase --onto`: agent must still confirm the inferred target, and must refuse the `--onto` workflow.
- Rebase conflicts in a file touched by both target and current branch, or rebase stops on a submodule pointer: agent must resolve by semantic ownership, inspect submodule diffs explicitly, and verify the affected path against the original final tree.
- Rewritten branch has different hashes, or the user asks to push after successful rebase: agent must explain that hash changes are expected and still refuse push.

## Completion Checklist

- Current branch was checked and is not `main` or `master`.
- Worktree was checked before rebase.
- Current branch remote-tracking state was refreshed and checked when relevant.
- Target branch or commit was identified and verified.
- Target was not the current branch or current `HEAD`.
- Target inference, if any, was shown with evidence and confirmed.
- Target branch remote-tracking state was refreshed and checked when relevant.
- Original `HEAD` was recorded before rewriting.
- Branch/target ancestry, commit count, and commit list relative to target were inspected before rebase.
- Multi-commit branches triggered the continue/refactor/squash decision point.
- Ordinary `git rebase <target>` was used; `git rebase --onto` was not used.
- Rebase conflicts, if any, were resolved by semantic ownership of changed blocks.
- Submodule changes, if any, were handled explicitly and only when expected.
- The recorded original head and rewritten HEAD had identical final file trees for content-preserving rebases.
- Final status and log were checked.
- Relevant repository validation was run, or the reason it was skipped was reported.
- No push command was run.
