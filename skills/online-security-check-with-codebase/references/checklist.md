# Security Assessment Checklist

Use this checklist to ensure complete coverage.

## Per-Endpoint Review

For every Swagger or OpenAPI endpoint, capture:

- Method and path
- Tag or subsystem
- Public, authenticated, admin, or `/internal`
- Auth mechanism
- Request identifiers such as `userId`, `tenantId`, `orgId`, `accountId`, `resourceId`
- Response fields that may include sensitive data
- Code entry point and downstream data access path

Check the endpoint for:

- Missing authentication
- Broken authorization or missing ownership checks
- Horizontal privilege escalation
- Vertical privilege escalation
- Missing tenant or organization scoping
- SQL or NoSQL injection
- Command, path, or template injection
- Reflected or stored XSS
- CSRF on cookie-based state-changing requests
- Sensitive data overexposure
- Insecure file upload, download, or path handling
- SSRF or unsafe outbound requests
- Open redirect or unsafe URL handling
- Excessive error detail or debug leakage

## Site-Level Review

Check the live site or API for:

- CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- Cookie flags such as `HttpOnly`, `Secure`, and `SameSite`
- CORS policy weaknesses
- Exposed Swagger or API docs
- Exposed `.git`, `.env`, backup archives, logs, or debug endpoints
- Directory listing or static file leakage
- TLS certificate issues and protocol weaknesses when observable
- Suspicious third-party scripts, injected links, or redirect behavior

## `/internal` Endpoint Rule

- Do not depend on live gateway probing for `/internal` endpoints.
- Review code-level authorization, caller trust, network assumptions, and data sensitivity.
- Flag any internal endpoint that would be high risk if accidentally exposed.
