#!/usr/bin/env python3
"""Collect and deduplicate read-only Git activity from multiple repositories."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def normalize_remote(remote: str) -> str:
    value = remote.strip()
    if not value:
        return ""

    scp_match = re.fullmatch(r"(?:[^@/]+@)?([^:/]+):(.+)", value)
    if scp_match and "://" not in value:
        host, path = scp_match.groups()
        normalized = f"{host.lower()}/{path.lstrip('/')}"
    elif "://" in value:
        parts = urlsplit(value)
        host = (parts.hostname or "").lower()
        port = f":{parts.port}" if parts.port else ""
        normalized = urlunsplit((parts.scheme.lower(), host + port, parts.path, "", ""))
    else:
        normalized = str(Path(os.path.expanduser(value)).resolve())

    return normalized.rstrip("/").removesuffix(".git")


def author_matches(name: str, email: str, filters: list[str]) -> bool:
    if not filters:
        return True
    candidates = {
        name.strip().casefold(),
        email.strip().casefold(),
        f"{name.strip()} <{email.strip()}>".casefold(),
    }
    return any(value.strip().casefold() in candidates for value in filters)


def collect_repository(
    supplied_path: str,
    since: str,
    until: str,
    authors: list[str],
) -> tuple[dict[str, object] | None, list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    repo = Path(os.path.expanduser(supplied_path)).resolve()

    if not repo.is_dir():
        return None, [], [f"Directory is not accessible: {supplied_path}"]

    inside = run_git(repo, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        detail = inside.stderr.strip() or "not a Git working tree"
        return None, [], [f"Skipped {supplied_path}: {detail}"]

    root_result = run_git(repo, "rev-parse", "--show-toplevel")
    if root_result.returncode != 0:
        return None, [], [f"Skipped {supplied_path}: cannot resolve repository root"]
    root = Path(root_result.stdout.strip()).resolve()

    remote_result = run_git(root, "remote", "get-url", "origin")
    remote = remote_result.stdout.strip() if remote_result.returncode == 0 else ""
    normalized_remote = normalize_remote(remote)
    if normalized_remote:
        repository_id = f"remote:{normalized_remote}"
    else:
        repository_id = f"local:{root}"
        warnings.append(f"No origin remote found for {root}; treating it as an independent repository")

    log_format = FIELD_SEPARATOR.join(["%H", "%cI", "%aI", "%an", "%ae", "%s"]) + RECORD_SEPARATOR
    log_result = run_git(
        root,
        "log",
        "--all",
        f"--since={since}",
        f"--until={until}",
        f"--format={log_format}",
    )
    if log_result.returncode != 0:
        detail = log_result.stderr.strip() or "git log failed"
        return None, [], warnings + [f"Could not read history for {root}: {detail}"]

    commits: list[dict[str, str]] = []
    for record in log_result.stdout.split(RECORD_SEPARATOR):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split(FIELD_SEPARATOR, 5)
        if len(fields) != 6:
            warnings.append(f"Ignored an unparseable commit record from {root}")
            continue
        sha, committed_at, authored_at, author_name, author_email, subject = fields
        if not author_matches(author_name, author_email, authors):
            continue
        commits.append(
            {
                "repository_id": repository_id,
                "sha": sha,
                "committed_at": committed_at,
                "authored_at": authored_at,
                "author_name": author_name,
                "author_email": author_email,
                "subject": subject,
                "source_path": str(root),
            }
        )

    repository = {
        "input_path": supplied_path,
        "root_path": str(root),
        "repository_id": repository_id,
        "origin_remote": remote or None,
        "normalized_remote": normalized_remote or None,
    }
    return repository, commits, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect read-only Git activity from caller-provided repositories."
    )
    parser.add_argument("--repo", action="append", required=True, help="Absolute repository directory; repeatable")
    parser.add_argument("--author", action="append", default=[], help="Exact Git author name or email; repeatable")
    parser.add_argument("--since", required=True, help="Inclusive lower time bound accepted by git log")
    parser.add_argument("--until", required=True, help="Inclusive upper time bound accepted by git log")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repositories: list[dict[str, object]] = []
    warnings: list[str] = []
    commits_by_key: dict[tuple[str, str], dict[str, object]] = {}

    for supplied_path in args.repo:
        repository, commits, repo_warnings = collect_repository(
            supplied_path, args.since, args.until, args.author
        )
        warnings.extend(repo_warnings)
        if repository is None:
            continue
        repositories.append(repository)
        for commit in commits:
            key = (commit["repository_id"], commit["sha"])
            existing = commits_by_key.get(key)
            if existing is None:
                item: dict[str, object] = dict(commit)
                source_path = item.pop("source_path")
                item["source_paths"] = [source_path]
                commits_by_key[key] = item
            else:
                source_path = commit["source_path"]
                source_paths = existing["source_paths"]
                if isinstance(source_paths, list) and source_path not in source_paths:
                    source_paths.append(source_path)

    commits = sorted(
        commits_by_key.values(),
        key=lambda item: (str(item["committed_at"]), str(item["repository_id"]), str(item["sha"])),
    )
    result = {
        "since": args.since,
        "until": args.until,
        "author_filters": args.author,
        "repositories": repositories,
        "commits": commits,
        "warnings": warnings,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if repositories else 2


if __name__ == "__main__":
    raise SystemExit(main())
