# Security Review Report Template

This template matches the worksheet fields described in [worksheet-conventions.md](worksheet-conventions.md).

## 1. Executive Summary

- Target:
- Environment:
- Review date:
- Inputs provided:
- Coverage summary:
- Highest-risk findings:

## 2. Scope And Constraints

- In-scope systems:
- Auth contexts used:
- Swagger or OpenAPI source:
- Codebase areas reviewed:
- Testing constraints:
- `/internal` handling note:

## 3. Methodology

- Endpoint inventory from Swagger or OpenAPI
- Code mapping from routes to implementation
- Static review categories applied
- Live verification techniques used
- Site-level configuration checks performed

## 4. Coverage Matrix

For each endpoint:

- Method and path
- Auth type
- Implementation file(s)
- Live tested: yes or no
- Result: no issue found, issue found, or needs follow-up

## 5. Findings

Repeat this section for each confirmed or likely issue.

### [Severity] Title

- Vulnerability type:
- Affected endpoint(s):
- Auth context required:
- Code location:
- Evidence:
- Exploit summary:
- Impact:
- Confidence:
- Remediation:

## 6. Endpoints Reviewed Without Findings

List endpoints reviewed with no confirmed issue, especially sensitive ones.

## 7. Open Questions And Follow-Up

- Areas not verified live
- Endpoints blocked by missing credentials or unsafe write semantics
- Ambiguous behaviors that need developer confirmation
