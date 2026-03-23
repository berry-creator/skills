#!/usr/bin/env python3
"""
Build a per-endpoint security review worksheet from either:
- an endpoint inventory JSON file produced by build_endpoint_inventory.py
- a raw Swagger/OpenAPI document
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_endpoint_inventory import build_rows, filter_rows, parse_spec, read_text  # noqa: E402

WORKSHEET_FIELDS = [
    "method",
    "path",
    "tags",
    "auth",
    "internal",
    "parameters",
    "request_body",
    "code_paths",
    "access_control",
    "xss",
    "injection",
    "csrf",
    "sensitive_data",
    "runtime_tested",
    "finding_status",
    "severity",
    "finding_title",
    "vulnerability_type",
    "confidence",
    "risk_focus",
    "evidence",
    "impact",
    "remediation",
    "notes",
]


def load_inventory(path: str) -> list[dict[str, str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Inventory JSON must be a list of endpoint rows")

    rows: list[dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        rows.append({str(key): "" if value is None else str(value) for key, value in entry.items()})
    return rows


def boolish(value: str) -> bool:
    return value.lower() in {"yes", "true", "1"}


def guess_risk_focus(row: dict[str, str]) -> str:
    focuses = []
    method = row.get("method", "").upper()
    path = row.get("path", "")
    auth = row.get("auth", "")
    has_body = boolish(row.get("request_body", ""))

    if row.get("internal") == "yes":
        focuses.append("internal trust boundary")
    if auth in {"none", "inherit"}:
        focuses.append("authn/authz")
    if "{" in path and "}" in path:
        focuses.append("idor")
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        focuses.append("state change")
    if has_body:
        focuses.append("injection")
    if any(token in path.lower() for token in ["search", "query", "filter", "export", "report"]):
        focuses.append("query injection")
    if any(token in path.lower() for token in ["html", "content", "template", "render", "comment", "message"]):
        focuses.append("xss")

    return ", ".join(dict.fromkeys(focuses)) or "standard review"


def build_sheet_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    worksheet = []

    for row in rows:
        method = row.get("method", "").upper()
        auth = row.get("auth", "")
        state_change = "yes" if method in {"POST", "PUT", "PATCH", "DELETE"} else "no"
        csrf_priority = "review" if state_change == "yes" and "cookie" in auth.lower() else "check if cookie auth"

        worksheet.append(
            {
                "method": row.get("method", ""),
                "path": row.get("path", ""),
                "tags": row.get("tags", ""),
                "auth": auth,
                "internal": row.get("internal", ""),
                "parameters": row.get("parameters", ""),
                "request_body": row.get("request_body", ""),
                "code_paths": "",
                "access_control": "pending",
                "xss": "pending",
                "injection": "pending",
                "csrf": csrf_priority,
                "sensitive_data": "pending",
                "runtime_tested": "no",
                "finding_status": "pending",
                "severity": "",
                "finding_title": "",
                "vulnerability_type": "",
                "confidence": "",
                "risk_focus": guess_risk_focus(row),
                "evidence": "",
                "impact": "",
                "remediation": "",
                "notes": "",
            }
        )

    return worksheet


def to_markdown(rows: list[dict[str, str]]) -> str:
    headers = [
        "Method",
        "Path",
        "Auth",
        "Internal",
        "Code Paths",
        "Access Control",
        "XSS",
        "Injection",
        "CSRF",
        "Sensitive Data",
        "Runtime Tested",
        "Finding Status",
        "Severity",
        "Finding Title",
        "Vuln Type",
        "Confidence",
        "Risk Focus",
        "Evidence",
        "Impact",
        "Remediation",
        "Notes",
    ]
    keys = [
        "method",
        "path",
        "auth",
        "internal",
        "code_paths",
        "access_control",
        "xss",
        "injection",
        "csrf",
        "sensitive_data",
        "runtime_tested",
        "finding_status",
        "severity",
        "finding_title",
        "vulnerability_type",
        "confidence",
        "risk_focus",
        "evidence",
        "impact",
        "remediation",
        "notes",
    ]

    lines = [
        f"# Security Review Worksheet ({len(rows)} endpoints)",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|").replace("\n", " ").strip() for key in keys]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines) + "\n"


def to_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=WORKSHEET_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a per-endpoint security review worksheet"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--inventory", help="Inventory JSON produced by build_endpoint_inventory.py")
    source.add_argument("--input", help="Raw Swagger/OpenAPI file path or URL")
    parser.add_argument(
        "--format",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument("--output", help="Optional output file path")
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Filter to operations containing this tag; repeatable",
    )
    parser.add_argument(
        "--path-prefix",
        action="append",
        default=[],
        help="Filter to paths with this prefix; repeatable",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.inventory:
            inventory_rows = load_inventory(args.inventory)
        else:
            spec = parse_spec(read_text(args.input))
            inventory_rows = build_rows(spec)

        inventory_rows = filter_rows(inventory_rows, args.tag, args.path_prefix)
        worksheet_rows = build_sheet_rows(inventory_rows)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        rendered = to_markdown(worksheet_rows)
    elif args.format == "csv":
        rendered = to_csv(worksheet_rows)
    else:
        rendered = json.dumps(worksheet_rows, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
