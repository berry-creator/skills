#!/usr/bin/env python3
"""
Generate an endpoint coverage inventory from a Swagger or OpenAPI document.

Supports:
- OpenAPI 3.x
- Swagger / OpenAPI 2.0
- Local files or remote URLs
- JSON directly
- YAML via PyYAML if available, otherwise Ruby stdlib YAML as fallback
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

HTTP_METHODS = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]


def read_text(source: str) -> str:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            encoding = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(encoding)

    return Path(source).read_text(encoding="utf-8")


def parse_yaml_with_ruby(text: str) -> Any:
    process = subprocess.run(
        [
            "ruby",
            "-r",
            "yaml",
            "-r",
            "json",
            "-e",
            "input = STDIN.read; data = YAML.safe_load(input, permitted_classes: [], aliases: true); puts JSON.generate(data)",
        ],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ValueError(process.stderr.strip() or "Ruby YAML parser failed")
    return json.loads(process.stdout)


def parse_spec(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except ModuleNotFoundError:
        data = parse_yaml_with_ruby(text)
        if isinstance(data, dict):
            return data

    raise ValueError("Unable to parse Swagger/OpenAPI document as JSON or YAML")


def normalize_security_names(security: Any) -> str:
    if security is None:
        return "inherit"
    if security == []:
        return "none"
    if not isinstance(security, list):
        return "unknown"

    names = []
    for requirement in security:
        if isinstance(requirement, dict):
            names.append(" + ".join(requirement.keys()))
    return " OR ".join(names) if names else "unknown"


def summarize_parameters(operation: dict[str, Any], path_item: dict[str, Any]) -> str:
    params = []
    seen = set()

    for entry in path_item.get("parameters", []) + operation.get("parameters", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        location = entry.get("in")
        if not name or not location:
            continue
        key = (name, location)
        if key in seen:
            continue
        seen.add(key)
        params.append(f"{location}:{name}")

    return ", ".join(params)


def has_request_body(operation: dict[str, Any]) -> str:
    if "requestBody" in operation:
        return "yes"

    for entry in operation.get("parameters", []):
        if isinstance(entry, dict) and entry.get("in") == "body":
            return "yes"

    return "no"


def first_line(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().splitlines()[0]


def filter_rows(
    rows: list[dict[str, str]],
    tags: list[str],
    prefixes: list[str],
) -> list[dict[str, str]]:
    filtered = rows
    if tags:
        wanted = set(tags)
        filtered = [
            row
            for row in filtered
            if wanted.intersection(
                {tag.strip() for tag in row["tags"].split(",") if tag.strip()}
            )
        ]

    if prefixes:
        filtered = [
            row for row in filtered if any(row["path"].startswith(prefix) for prefix in prefixes)
        ]

    return filtered


def build_rows(spec: dict[str, Any]) -> list[dict[str, str]]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("Swagger/OpenAPI document does not contain a valid 'paths' object")

    root_security = spec.get("security")
    rows = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            op_security = operation.get("security", root_security)
            tags = operation.get("tags") or []
            summary = operation.get("summary") or first_line(operation.get("description"))

            rows.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "tags": ", ".join(tags) if isinstance(tags, list) else "",
                    "auth": normalize_security_names(op_security),
                    "internal": "yes" if "/internal" in path else "no",
                    "operation_id": operation.get("operationId", ""),
                    "summary": summary or "",
                    "parameters": summarize_parameters(operation, path_item),
                    "request_body": has_request_body(operation),
                    "review_status": "pending",
                }
            )

    rows.sort(key=lambda row: (row["path"], row["method"]))
    return rows


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def to_markdown(rows: list[dict[str, str]]) -> str:
    headers = [
        "Method",
        "Path",
        "Tags",
        "Auth",
        "Internal",
        "Operation ID",
        "Summary",
        "Parameters",
        "Body",
        "Review Status",
    ]
    keys = [
        "method",
        "path",
        "tags",
        "auth",
        "internal",
        "operation_id",
        "summary",
        "parameters",
        "request_body",
        "review_status",
    ]

    lines = [
        f"# Endpoint Inventory ({len(rows)} endpoints)",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(markdown_escape(row[key]) for key in keys) + " |")

    return "\n".join(lines) + "\n"


def to_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "method",
        "path",
        "tags",
        "auth",
        "internal",
        "operation_id",
        "summary",
        "parameters",
        "request_body",
        "review_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an endpoint inventory from a Swagger/OpenAPI document"
    )
    parser.add_argument("--input", required=True, help="Local file path or remote URL")
    parser.add_argument(
        "--format",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path; prints to stdout when omitted",
    )
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
        text = read_text(args.input)
        spec = parse_spec(text)
        rows = build_rows(spec)
        rows = filter_rows(rows, args.tag, args.path_prefix)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        rendered = to_markdown(rows)
    elif args.format == "csv":
        rendered = to_csv(rows)
    else:
        rendered = json.dumps(rows, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
