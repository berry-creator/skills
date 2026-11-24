---
name: organizing-git-commit-messages
description: Use when drafting or organizing Git commit messages for uncommitted changes, one commit, a commit range, or changes through origin/main, including explicit requests to commit, amend, or reword.
---

# Organizing Git Commit Messages

Analyze actual Git changes and summarize them by business capability or technical boundary.
Use the fixed Markdown format below across repositories, with the current branch in both branch fields.

## Scope

Handle message drafting and explicitly requested normal commits or single-commit message rewrites.
For a parent history-editing workflow, supply message content and attribution decisions while
leaving the history operation to that workflow. Standalone range analysis produces a proposal only.

## Target Resolution

1. Read repository instructions and run `git status --short`.
2. Resolve the user's requested files, staged changes, commit, or range. Without an explicit target,
   inspect staged, unstaged, and untracked work. If the worktree is clean, use `HEAD` and disclose it.
3. Preserve Git range semantics. `A..B` excludes `A`. An explicitly inclusive range from `A` through
   `B` uses `A^..B`. For a root start commit, include its initial tree changes without referencing `A^`.
4. For changes through `origin/main`, fetch with `git fetch origin main` only when latest remote
   state is requested or implied. Record the exact endpoint hash. If fetching is disallowed or
   fails, disclose unverified freshness before using the local remote-tracking ref.

## Evidence Collection

Read changed paths, diff statistics, actual diffs, and relevant source files. Include public APIs,
persistence, messaging, jobs, configuration, tests, documentation, and deployment behavior when touched.
Inspect both staged and unstaged diffs when included, and read in-scope untracked files.

Read complete existing messages with `git show -s --format='%H%n%B' <commit>` or
`git log --format='%H%n%B%n---END-COMMIT---' <range>`. For ranges, inspect the aggregate diff and
individual commits when needed to understand intermediate or reverted changes. A net diff alone
can hide work that was subsequently reverted. Describe the resulting behavior accurately.

## Grouping

Choose section labels by business capability first, then by technical boundary. Keep related API,
implementation, configuration, documentation, and tests in one section when they implement one behavior.
Use one section for a focused change and additional sections for independently understandable changes.
Describe concrete outcomes, compatibility changes, and failure or retry behavior visible in the diff.

Use repository guidance and any existing commit-message profile for domain vocabulary and path hints.
Profiles are optional and need no new configuration file. Determine capabilities from behavior,
rather than grouping files by extension. Follow templates through generated files when touched,
summarizing shared behavior once and identifying meaningful deviations.

## Attribution

Resolve branch and message author independently.

- `branch-name` always comes from `git branch --show-current`, including when organizing existing
  commits or ranges. In detached HEAD, use `detached-<short-hash>` from `git rev-parse --short HEAD`.
  Historical task names or branch labels are replaced with this current branch value in both fields.
- `message-author` uses an explicit user value first. For an existing commit, preserve a complete
  historical author label from a first-line `[<old-context>][<message-author>] ` prefix.
  For a range, inherit it when all selected commits have the same complete author label.
- For new work or existing commits with no attribution at all, use `git config user.name`, then
  `git config user.email`, then `unknown-author`. Disclose this fallback for existing commits.
- For conflicting, partial, malformed, or mixed present/absent historical author labels, return
  `needs decision` and ask only for the unresolved author field before producing the final message.
  Different historical branch labels are resolved by the current-branch rule.

The message author is a text label. Preserve real Git Author metadata separately during a rewrite.

## Commit Message Format

```markdown
[<branch-name>][<message-author>] <short overall summary>

**<business capability or technical boundary>**
- <specific behavior change>
- <specific behavior change>

**<business capability or technical boundary>**
- <specific behavior change>

 #<branch-name>
```

- Keep exactly one space after the second closing bracket and a concise summary on the first line.
- Include at least one bold section label followed immediately by its first bullet.
- Keep bullets adjacent within a section and exactly one blank line between sections.
- Keep exactly one blank line before the final branch line and one leading space before `#`.
- Use the same resolved branch value in the first line and the final line.
- Keep this structure across projects. Repository vocabulary and optional profiles guide section
  content. Every message retains its prefix, summary, Markdown sections, bullets, and branch footer.

## Output Language

Write summaries, section labels, and bullets in the language explicitly requested by the user,
otherwise in the language of the user's request. If that is unclear, use the conversation's language.
Preserve exact branch names, author labels, API identifiers, and product names.

## Mutation Safety

- Never run `git push` or force-push.
- Standalone range analysis is output-only. Never squash, merge, drop, reorder, or rewrite a range
  under this skill.
- Create a normal commit only when explicitly requested. Stage only in-scope content.
- Amend or reword one commit only when explicitly requested. For `HEAD`, use a message-only amend
  that excludes staged content, such as `git commit --amend --only --file <message-file>`.
  For an older commit, preserve descendant trees and topology when selecting a reword procedure.
- Before rewriting, check `git status --short`, remote branches containing the commit with
  `git branch -r --contains <commit>`, and the current upstream. Explain published-history
  consequences and obtain any missing authorization, reusing informed authorization already given.
- Preserve unrelated staged, unstaged, and untracked content, the target tree, and original Author
  identity and AuthorDate. Follow repository identity rules for new commits. Never use `--reset-author`.
- Pass raw message content to Git using a message file and `--cleanup=verbatim` to preserve spacing
  and the branch footer. Resolve interference from an active Git operation before starting another.

## Output

Display a proposed message as exactly one `markdown` fenced code block containing the complete
message. For draft-only requests, this block is the final response except for necessary clarification,
fallback disclosure, target identification, or remote-freshness limitations. When writing to Git,
remove the fences and preserve the message content. After an authorized mutation, report its result.

## Verification

Before output, verify branch and author sources, requested language, capability coverage, and every
format rule. After a mutation, inspect status, recent log, and the full stored message. For a rewrite,
compare the target tree and Author metadata before and after, and verify unrelated work was preserved.
Report the resulting commit and any verification limits. State that no push was performed.
