# Worksheet Conventions

Use these values consistently so the worksheet can be turned into a reliable report.

## `finding_status`

- `pending`: not fully reviewed yet
- `confirmed`: vulnerability supported by code evidence, runtime evidence, or both
- `likely`: strong evidence exists but some verification is still limited
- `follow_up`: suspicious behavior or incomplete coverage that needs more work
- `blocked`: could not complete because of missing access, unsafe write semantics, or another hard constraint
- `no_issue`: reviewed and no confirmed issue found

## `severity`

- `critical`: immediate account, tenant, admin, or sensitive-data compromise
- `high`: serious privilege escalation, injection, or data exposure with strong exploitability
- `medium`: meaningful security weakness with constrained impact or preconditions
- `low`: limited impact or defense-in-depth issue
- `info`: noteworthy observation, low-risk misconfiguration, or hardening recommendation

## Evidence Fields

- `code_paths`: router, controller, service, repository, model, template, or middleware paths used to support the finding
- `evidence`: concise proof, such as a code condition, HTTP response, missing guard, reflected payload, or leaked field
- `notes`: exploit path, follow-up details, unresolved questions, or runtime caveats
- `impact`: what an attacker gains
- `remediation`: the concrete repair direction
- `confidence`: use simple values such as `high`, `medium`, or `low`
