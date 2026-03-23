---
name: online-security-check-with-codebase
description: Use when auditing a web app or API with a live URL, HTTP auth headers or cookies, Swagger or OpenAPI docs, and the current codebase to assess endpoint-level and site-level security issues such as broken access control, XSS, injection, CSRF, sensitive data exposure, unsafe security headers, and to produce a remediation report.
---

# Online Security Check With Codebase

## Overview

Use this skill when the user wants a combined black-box, gray-box, and code-assisted security review of a web application. The core job is to turn the Swagger or OpenAPI contract plus the live target plus the current codebase into a verified security assessment and a repair-ready report.

Read [references/checklist.md](references/checklist.md) when you need the full assessment matrix. Use [references/report-template.md](references/report-template.md) to structure the final report.
Use `scripts/build_endpoint_inventory.py` to generate the initial endpoint coverage matrix from Swagger or OpenAPI before reviewing the codebase.
Use `scripts/build_security_review_sheet.py` to expand that coverage matrix into an endpoint-by-endpoint security worksheet.
Use [references/worksheet-conventions.md](references/worksheet-conventions.md) to keep worksheet statuses and severities consistent.
Use `scripts/build_security_report.py` to turn a completed worksheet into a first-pass remediation report.

## Required Inputs

Gather these before testing:

- Target base URL or environment URL
- HTTP authentication material the user provides
- Swagger or OpenAPI document location or file
- The system, service, or module in scope if the Swagger file contains multiple domains
- Any explicit safety constraints for write actions

If one of these is missing, proceed with the parts you can complete and clearly label the gaps.

## Safety And Scope Rules

- Treat the work as an authorized assessment for the user-provided target only.
- Prefer read-only and idempotent requests first.
- Do not perform destructive actions, bulk data mutation, account takeover, or denial-of-service style testing unless the user explicitly asks for it.
- Use minimal-impact payloads that establish whether a class of vulnerability is likely present.
- Endpoints containing `/internal` are internal-only. Do not rely on live gateway testing for those endpoints; review their code paths, trust assumptions, and call sites instead.
- Do not claim a vulnerability from intuition alone. Support each finding with code evidence, runtime evidence, or both.

## Workflow

### 1. Build The Endpoint Inventory

Read the Swagger or OpenAPI definition and extract, for each endpoint:

- Method and path
- Auth scheme and required headers
- Request parameters, body schema, and object identifiers
- Response schema and sensitive fields
- Tag, service, or module ownership
- Whether the path is public, user-facing, admin-only, or `/internal`

Create a working table so every endpoint is accounted for.

When the API description is large, start with:

```bash
python3 skills/online-security-check-with-codebase/scripts/build_endpoint_inventory.py \
  --input /path/to/openapi.yaml \
  --format markdown
```

Then generate the worksheet Claude can fill during review:

```bash
python3 skills/online-security-check-with-codebase/scripts/build_endpoint_inventory.py \
  --input /path/to/openapi.yaml \
  --format json \
  --output /tmp/inventory.json

python3 skills/online-security-check-with-codebase/scripts/build_security_review_sheet.py \
  --inventory /tmp/inventory.json \
  --format markdown
```

When you have completed the worksheet, draft the report with:

```bash
python3 skills/online-security-check-with-codebase/scripts/build_security_report.py \
  --worksheet /path/to/worksheet.csv \
  --target https://app.example.com \
  --environment production \
  --swagger-source /path/to/openapi.yaml
```

If the Swagger file covers multiple systems, narrow it with repeated `--tag` or `--path-prefix` filters, then review the resulting subset endpoint by endpoint.

### 2. Map Each Endpoint To The Codebase

For every endpoint in scope:

- Find router, controller, handler, service, repository, and model code
- Identify authentication, authorization, and tenancy checks
- Identify validation and schema enforcement
- Identify raw SQL, dynamic query building, template rendering, file handling, command execution, or outbound requests
- Identify caches, background jobs, or downstream internal service calls that affect authorization or data exposure

Use fast text search first, then read the exact implementation. Do not stop at route registration.

### 3. Perform Static Security Review Per Endpoint

Review every endpoint for at least these classes:

- Broken access control: horizontal privilege escalation, vertical privilege escalation, IDOR, missing tenant scoping, role bypass, unsafe trust in client-supplied IDs
- Injection: SQL, NoSQL, template, command, path, or unsafe interpreter usage
- XSS: reflected, stored, DOM-adjacent, unsafe HTML or markdown rendering, unescaped values in templates
- CSRF: cookie-authenticated state-changing endpoints without CSRF protection, origin validation, or same-site protections
- Authentication and session flaws: missing auth, weak token validation, insecure cookie flags, replayable tokens, weak logout or refresh flows
- Sensitive data exposure: secrets, tokens, PII, internal stack traces, debug data, or overbroad response fields
- Upload, file, redirect, and SSRF-style issues when those behaviors exist

When reviewing `/internal` endpoints, focus on whether internal trust assumptions could become dangerous if the endpoint is later exposed or is reachable through a compromised internal caller.

### 4. Perform Live Verification Against The Target

Use the provided URL and auth headers or cookies to confirm what the code review suggests.

Recommended live checks:

- Establish a baseline valid request for each auth context
- Probe object-level authorization by varying IDs, tenant identifiers, owner identifiers, or pagination cursors
- Probe role boundaries by comparing privileged and unprivileged identities when available
- Try benign malformed input to test validation and injection resistance
- Inspect reflected or rendered output for unsanitized values
- Inspect CORS, cookies, CSP, HSTS, frame protections, cache controls, and other security headers
- Check for exposed assets such as Swagger UIs, backup files, `.git`, `.env`, or verbose error pages if they are in scope

For state-changing endpoints, prefer harmless mutations, dry-run modes, validation-only modes, or clearly reversible requests. If safe runtime verification is not possible, document the finding as code-backed but runtime-unverified.

### 5. Expand To Site-Level And Platform Checks

Cover broader web and deployment issues around the application:

- OWASP Top 10 application-layer weaknesses
- Content tampering indicators such as suspicious external scripts, unexpected redirects, or injected links
- Security header and TLS posture
- Sensitive file exposure and asset discovery
- Framework, middleware, or dependency fingerprints that indicate known risk areas

Limit claims about malware, compromise, or black links unless you have direct evidence from the target or repository.

### 6. Produce A Repair-Ready Report

Use [references/report-template.md](references/report-template.md). The report should include:

- Executive summary
- Scope, inputs, and testing limits
- Endpoint inventory coverage
- Findings sorted by severity
- For each finding: affected endpoint, vulnerability type, exploit path, evidence, code location, impact, confidence, and remediation guidance
- A clear list of endpoints reviewed but not found vulnerable
- Open questions and unverified areas

If you are using the generated worksheet, prefer CSV or JSON while collecting findings so `scripts/build_security_report.py` can turn it into a draft report automatically.

## Evidence Standards

- Prefer findings that are supported by both code and runtime evidence.
- If a finding is code-only, say why runtime verification was skipped or unsafe.
- If a runtime symptom appears but code evidence is inconclusive, downgrade confidence and explain the ambiguity.
- Include concrete file references and affected endpoint paths in the final report.

## Working Style

- Be systematic rather than opportunistic. The user asked for endpoint-by-endpoint coverage.
- Track coverage explicitly so no Swagger endpoint is skipped by accident.
- When results are contradictory, use the same evidence-first mindset as `systematic-debugging`.
- Before finalizing, do one verification pass on the report to ensure each claim has supporting evidence and a clear remediation path.
