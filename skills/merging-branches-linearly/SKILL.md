---
name: merging-branches-linearly
description: Use when merging the current Git branch into another branch while preserving the repository's branch-history policy, especially when the target branch may need to be inferred.
---

# Merging Branches Linearly

## Overview

Merge the current branch into a target branch while preserving the repository's branch-history policy. Target branches `main` and `master` are special: they must receive a new `--no-ff` merge commit. Other target branches must be updated by fast-forward only after the source branch is based on the target.

## Safety Rules

- Never run plain `git merge <branch>` unless the target branch is literal `main` or `master` and the command is creating the required integration commit with `--no-ff`.
- Never run `git push`, `git push -f`, or `git push --force-with-lease`.
- Before switching, rebasing, or merging, run `git status --short --branch`; if dirty, stop.
- The source branch is the current branch unless the user explicitly says otherwise.
- If no target branch was provided, analyze target candidates, show the evidence, and get user confirmation before changing branches.
- Do not integrate a branch into itself.
- If the target has a remote-tracking branch or target inference depends on remote refs, fetch that target ref before integration. Do not reset local branches; if local and remote target diverge, stop and ask.

## When to Use

- The user asks to merge, integrate, land, or bring the current branch into a target branch.
- The user gives a target branch and wants current branch changes applied there.
- The user asks to merge current branch but does not name the target branch.

Do not use this for squashing commit ranges, changing commit messages, or pushing integrated branches.

## Strategy Table

| Target branch | Required strategy | Commit behavior |
| --- | --- | --- |
| `main` or `master` | Rebase source onto target, then `git merge --no-ff <source>` on target | Must create one new merge commit |
| Any other target | Rebase source onto target, then `git merge --ff-only <source>` on target | Must not create a new commit |

For literal branch names `main` and `master`, the `--no-ff` merge commit is the allowed exception to the linear-history rule. Branches named `trunk`, `develop`, `release/*`, or anything else use the non-main/master strategy unless the user explicitly changes the policy. For all other targets, merge commits are not allowed.

## Target Branch Analysis

If the user did not provide a target branch:

1. Inspect branch context:

```sh
git status --short --branch
git branch -vv
git remote -v
git branch --all
```

2. Consider candidates such as explicit upstream, `origin/HEAD`, `origin/main`, `origin/master`, release branches, develop branches, and long-lived branches related by naming or merge-base.
3. Compare candidates with:

```sh
git merge-base HEAD <candidate>
git log --oneline --decorate <candidate>..HEAD
git log --oneline --decorate HEAD..<candidate>
```

4. Present the inferred target branch, evidence, source branch, expected strategy, and whether a new commit will be created.
5. Continue only after the user confirms. If multiple candidates are plausible, ask the user to choose.

## Workflow

1. Check state:

```sh
git status --short --branch
git branch --show-current
```

2. Determine source and target. Stop if source equals target.
3. If the target was inferred, get user confirmation.
4. Refresh the target when it has a remote counterpart or remote freshness affects the decision:

```sh
git fetch origin <target-name>
git switch <target>
git rev-parse HEAD
git rev-parse origin/<target-name>
git merge-base --is-ancestor HEAD origin/<target-name>
```

If the local target can fast-forward to its remote counterpart, update it while still on the target branch:

```sh
git merge --ff-only origin/<target-name>
```

If the local target and remote target have diverged, stop and ask. Do not use `git reset`. If the target has no remote counterpart, skip this remote-refresh step and state that the local target is being used.

5. Rebase source onto target:

```sh
git switch <source>
git rebase <target>
```

6. Switch back to target:

```sh
git switch <target>
```

7. Integrate according to target type:

```sh
# target is main/master
git merge --no-ff <source>

# target is not main/master
git merge --ff-only <source>
```

8. Verify:

```sh
git status --short --branch
git log --oneline --decorate -n 10
```

9. Tell the user the integration completed and that no push was performed.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Running plain `git merge <branch>` for a non-main/master target | Use `--no-ff` only for `main/master`; use `--ff-only` for all other targets. |
| Treating `main/master` merge commit as violating the rule | It is the required exception: create one `--no-ff` integration commit. |
| Creating a merge commit on release/feature/develop/trunk branches | Do not. Only literal `main` and `master` use `--no-ff`; all others use `--ff-only`. |
| Guessing target branch when user omitted it | Analyze candidates with fresh remote refs when relevant, show evidence, and wait for confirmation. |
| Pushing after integration | Never push from this skill. |
| Rebasing with dirty worktree | Stop until the worktree is clean. |

## Pressure Scenarios for Skill Verification

- User asks to integrate into `release/*`: agent must rebase source onto target and use `git merge --ff-only`, not plain merge or `--no-ff`.
- User asks to integrate into `main` with a new commit: agent must use `git merge --no-ff` after rebasing source onto main.
- User says "merge back to trunk" without naming a target: agent must analyze candidates with fresh refs when relevant and wait for confirmation; `trunk` is not automatically treated as `main/master`.
- User asks to push after integration: agent must refuse push.
- User has dirty worktree: agent must stop before switching/rebasing/merging.

## Completion Checklist

- Source branch and target branch identified.
- Target inference, if any, was shown with evidence and confirmed.
- Worktree was clean before write operations.
- Remote target freshness was checked when the target has a remote counterpart; divergent local/remote target stopped the workflow.
- Source was rebased onto target before integration.
- `main/master` target used `git merge --no-ff` and created a merge commit.
- Non-`main/master` target used `git merge --ff-only` and created no commit.
- No plain `git merge <branch>` was run for non-`main/master` targets.
- Final status and log were checked.
- No push command was run.
