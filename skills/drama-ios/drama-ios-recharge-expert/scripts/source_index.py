#!/usr/bin/env python3
"""Deterministic, read-only recharge source evidence index."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


PRODUCER_PATTERNS = ("POST_NOTIFY", "postNotificationName", "ATHDispatchEvent")
CONSUMER_PATTERNS = ("ADD_NOTIFY", "HANDLER_NOTIFY", "addObserver", "subscribe_")
DECLARATION_PATTERNS = ("EXTERN_KEY", "DECLARE_KEY", "ATHDeclareEvent", "ATHDefineEvent")
SOURCE_SUFFIXES = {
    ".h", ".m", ".mm", ".swift", ".c", ".cc", ".cpp", ".py", ".rb",
    ".js", ".jsx", ".ts", ".tsx", ".json", ".yaml", ".yml", ".md",
    ".plist", ".proto",
}
EXCLUDED_PREFIXES = (
    "Cores/pbobjc/",
    "SDK/TurnoverSDK/Protocs/",
    "confuse/",
    "ir_mapping/",
)
SYMBOL_PATTERNS = (
    re.compile(r"^\s*[+-]\s*\([^)]*\)\s*([^\{;]+)"),
    re.compile(r"^\s*@(?:interface|implementation|protocol)\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*(?:static\s+)?(?:const\s+)?[A-Za-z_][\w<>\s*]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)"),
    re.compile(r"^\s*(?:#define|DECLARE_[A-Z_]+|EXTERN_[A-Z_]+)\s*\(?\s*([A-Za-z_][A-Za-z0-9_]*)"),
)
EVIDENCE_CATEGORIES = (
    "exact_matches",
    "event_evidence",
    "historical_cochange",
    "name_similarity",
)
DEFAULT_MAX_RESULTS = 60
DEFAULT_MAX_CHARS = 12000


class GitError(RuntimeError):
    pass


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or "git command failed")
    return result


def repository_root(path: Path) -> Path:
    result = run_git(path, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def validate_revision(repo: Path, revision: str | None) -> str | None:
    if not revision:
        return None
    result = run_git(repo, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    return result.stdout.strip()


def tracked_paths(repo: Path, revision: str | None) -> list[str]:
    if revision:
        output = run_git(repo, ["ls-tree", "-r", "--name-only", revision]).stdout
    else:
        output = run_git(repo, ["ls-files"]).stdout
    return sorted(
        path for path in output.splitlines()
        if Path(path).suffix.lower() in SOURCE_SUFFIXES
        and not path.startswith(EXCLUDED_PREFIXES)
    )


def file_text(repo: Path, path: str, revision: str | None, cache: dict[str, str]) -> str:
    cache_key = f"{revision or 'WORKTREE'}:{path}"
    if cache_key in cache:
        return cache[cache_key]
    if revision:
        result = run_git(repo, ["show", f"{revision}:{path}"], check=False)
        text = result.stdout if result.returncode == 0 else ""
    else:
        candidate = repo / path
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            text = ""
    cache[cache_key] = text
    return text


def enclosing_symbol(lines: list[str], line_number: int) -> str:
    for index in range(min(line_number - 1, len(lines) - 1), -1, -1):
        line = lines[index]
        for pattern in SYMBOL_PATTERNS:
            match = pattern.match(line)
            if match:
                return " ".join(match.group(1).split())
    return "<file-scope>"


def exact_kind(query: str, content: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", query):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(query)}(?![A-Za-z0-9_])", content):
            return "symbol_or_key"
    return "literal"


def git_grep(repo: Path, query: str, revision: str | None) -> list[tuple[str, int, str]]:
    args = ["grep", "-n", "-I", "-F", "-e", query]
    if revision:
        args.append(revision)
    args.extend([
        "--",
        ".",
        ":(exclude)Cores/pbobjc/**",
        ":(exclude)SDK/TurnoverSDK/Protocs/**",
        ":(exclude)confuse/**",
        ":(exclude)ir_mapping/**",
    ])
    result = run_git(repo, args, check=False)
    if result.returncode not in (0, 1):
        raise GitError(result.stderr.strip() or "git grep failed")
    matches: list[tuple[str, int, str]] = []
    prefix = f"{revision}:" if revision else ""
    for raw_line in result.stdout.splitlines():
        line = raw_line[len(prefix):] if prefix and raw_line.startswith(prefix) else raw_line
        match = re.match(r"^(.+?):(\d+):(.*)$", line)
        if match:
            matches.append((match.group(1), int(match.group(2)), match.group(3).strip()))
    return matches


def classify_event_role(content: str) -> str | None:
    if content.lstrip().startswith(("//", "/*", "*")):
        return None
    if any(pattern in content for pattern in PRODUCER_PATTERNS):
        return "producer"
    if any(pattern in content for pattern in CONSUMER_PATTERNS):
        return "consumer"
    if any(pattern in content for pattern in DECLARATION_PATTERNS):
        return "declaration"
    return None


def collect_exact(repo: Path, queries: list[str], revision: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cache: dict[str, str] = {}
    exact: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int, str]] = set()
    for query in sorted(set(queries)):
        for path, line_number, content in git_grep(repo, query, revision):
            key = (query, path, line_number, content)
            if key in seen:
                continue
            seen.add(key)
            lines = file_text(repo, path, revision, cache).splitlines()
            item = {
                "query": query,
                "match_kind": exact_kind(query, content),
                "path": path,
                "line": line_number,
                "source_identity": f"{path}:{line_number}",
                "symbol": enclosing_symbol(lines, line_number),
                "content": content,
            }
            exact.append(item)
            role = classify_event_role(content)
            if role:
                events.append({**item, "role": role})
    sort_key = lambda item: (item["query"], item["path"], item["line"], item["content"])
    return sorted(exact, key=sort_key), sorted(events, key=lambda item: (item["query"], item["role"], item["path"], item["line"]))


def commit_paths(repo: Path, commit: str) -> list[str]:
    result = run_git(repo, ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit])
    return sorted(set(result.stdout.splitlines()))


def historical_cochange(repo: Path, seed_paths: list[str], revision: str | None, history_limit: int) -> list[dict[str, Any]]:
    if not seed_paths or history_limit <= 0:
        return []
    args = ["log", f"--max-count={history_limit}", "--format=%H"]
    if revision:
        args.append(revision)
    args.extend(["--", *sorted(seed_paths)[:8]])
    commits = [line for line in run_git(repo, args).stdout.splitlines() if line]
    counts: Counter[str] = Counter()
    witnesses: dict[str, list[str]] = defaultdict(list)
    seed_set = set(seed_paths)
    for commit in commits:
        for path in commit_paths(repo, commit):
            if path in seed_set:
                continue
            counts[path] += 1
            witnesses[path].append(commit)
    return [
        {
            "path": path,
            "source_identity": path,
            "shared_commit_count": count,
            "commits": sorted(witnesses[path]),
            "confidence": "investigation_lead_only",
        }
        for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def name_similarity(paths: list[str], queries: list[str], excluded_paths: set[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in paths:
        if path in excluded_paths:
            continue
        lower_path = path.lower()
        tokens = [token for token in re.split(r"[^a-z0-9]+", lower_path) if token]
        stem = Path(path).stem.lower()
        for query in sorted(set(queries)):
            query_lower = query.lower()
            scores = [difflib.SequenceMatcher(None, query_lower, stem).ratio()]
            scores.extend(difflib.SequenceMatcher(None, query_lower, token).ratio() for token in tokens)
            score = max(scores, default=0.0)
            if score < 0.58:
                continue
            candidates.append({
                "query": query,
                "path": path,
                "source_identity": path,
                "score": round(score, 3),
                "confidence": "low",
                "use": "investigation_appendix_only",
            })
    return sorted(candidates, key=lambda item: (item["query"], -item["score"], item["path"]))


def stratum_key(category: str, item: dict[str, Any]) -> tuple[str, ...]:
    query = item.get("query")
    if not isinstance(query, str):
        return ()
    if category == "event_evidence":
        return (query, str(item.get("role", "unknown")))
    return (query,)


def round_robin_paths(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for item in items:
        by_path[str(item.get("path", "<unknown>"))].append(item)
    ordered: list[dict[str, Any]] = []
    while any(by_path.values()):
        for path in sorted(by_path):
            if by_path[path]:
                ordered.append(by_path[path].popleft())
    return ordered


def serialized_item_chars(item: dict[str, Any]) -> int:
    return len(json.dumps(item, ensure_ascii=False, sort_keys=True))


def deterministic_item_key(item: dict[str, Any]) -> tuple[int, str]:
    serialized = json.dumps(item, ensure_ascii=False, sort_keys=True)
    return len(serialized), serialized


def query_coverage_key(item: dict[str, Any]) -> tuple[str, ...] | None:
    query = item.get("query")
    return (query,) if isinstance(query, str) else None


def role_coverage_key(category: str, item: dict[str, Any]) -> tuple[str, ...] | None:
    if category != "event_evidence":
        return None
    query = item.get("query")
    if not isinstance(query, str):
        return None
    return query, str(item.get("role", "unknown"))


def path_coverage_key(category: str, item: dict[str, Any]) -> tuple[str, ...] | None:
    query = item.get("query")
    if not isinstance(query, str):
        return None
    path = str(item.get("path", "<unknown>"))
    if category == "event_evidence":
        return query, str(item.get("role", "unknown")), path
    return query, path


def select_coverage_phase(
    items: list[dict[str, Any]],
    group_key,
    selected_ids: set[int],
    returned: list[dict[str, Any]],
    used_chars: int,
    max_results: int,
    max_chars: int,
) -> int:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        key = group_key(item)
        if key is not None:
            grouped[key].append(item)

    proposals: list[tuple[tuple[str, ...], dict[str, Any], int]] = []
    for key in sorted(grouped):
        if any(id(item) in selected_ids for item in grouped[key]):
            continue
        available = [item for item in grouped[key] if id(item) not in selected_ids]
        if not available:
            continue
        candidate = min(available, key=deterministic_item_key)
        proposals.append((key, candidate, serialized_item_chars(candidate)))

    remaining_results = max_results - len(returned)
    remaining_chars = max_chars - used_chars
    all_fit = (
        len(proposals) <= remaining_results
        and sum(item_chars for _, _, item_chars in proposals) <= remaining_chars
    )
    ordered = (
        sorted(proposals, key=lambda proposal: proposal[0])
        if all_fit
        else sorted(proposals, key=lambda proposal: (proposal[2], proposal[0], deterministic_item_key(proposal[1])[1]))
    )
    for _, item, item_chars in ordered:
        if len(returned) >= max_results:
            break
        if used_chars + item_chars > max_chars:
            continue
        returned.append(item)
        selected_ids.add(id(item))
        used_chars += item_chars
    return used_chars


def coverage_metadata(
    category: str,
    items: list[dict[str, Any]],
    returned: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], bool]:
    if not any("query" in item for item in items):
        return [], [], False
    found: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    selected: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in items:
        found[stratum_key(category, item)][str(item.get("path", "<unknown>"))] += 1
    for item in returned:
        selected[stratum_key(category, item)][str(item.get("path", "<unknown>"))] += 1
    strata: list[dict[str, Any]] = []
    uncovered: list[dict[str, str]] = []
    for key in sorted(found):
        query = key[0]
        role = key[1] if len(key) > 1 else None
        path_counts = [
            {
                "path": path,
                "found": found[key][path],
                "returned": selected[key][path],
                "coverage_met": selected[key][path] > 0,
            }
            for path in sorted(found[key])
        ]
        summary: dict[str, Any] = {
            "query": query,
            "found": sum(found[key].values()),
            "returned": sum(selected[key].values()),
            "paths": path_counts,
        }
        if role is not None:
            summary["role"] = role
        summary["uncovered_paths"] = [item["path"] for item in path_counts if not item["coverage_met"]]
        summary["coverage_met"] = not summary["uncovered_paths"]
        strata.append(summary)
        for path in summary["uncovered_paths"]:
            uncovered_item = {"query": query, "path": path}
            if role is not None:
                uncovered_item["role"] = role
            uncovered.append(uncovered_item)
    return strata, uncovered, bool(uncovered)


def limit_category(
    category: str,
    items: list[dict[str, Any]],
    max_results: int,
    max_chars: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    returned: list[dict[str, Any]] = []
    used_chars = 0
    selected_ids: set[int] = set()

    used_chars = select_coverage_phase(
        items,
        query_coverage_key,
        selected_ids,
        returned,
        used_chars,
        max_results,
        max_chars,
    )
    used_chars = select_coverage_phase(
        items,
        lambda item: role_coverage_key(category, item),
        selected_ids,
        returned,
        used_chars,
        max_results,
        max_chars,
    )
    used_chars = select_coverage_phase(
        items,
        lambda item: path_coverage_key(category, item),
        selected_ids,
        returned,
        used_chars,
        max_results,
        max_chars,
    )

    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if id(item) not in selected_ids:
            grouped[stratum_key(category, item)].append(item)
    queues = {
        key: deque(round_robin_paths(grouped[key]))
        for key in sorted(grouped)
    }
    candidates: list[dict[str, Any]] = []
    while any(queues.values()):
        for key in sorted(queues):
            if queues[key]:
                candidates.append(queues[key].popleft())
    for item in candidates:
        if len(returned) >= max_results:
            break
        item_chars = serialized_item_chars(item)
        if used_chars + item_chars > max_chars:
            continue
        returned.append(item)
        selected_ids.add(id(item))
        used_chars += item_chars
    strata, uncovered_strata, coverage_unmet = coverage_metadata(category, items, returned)
    metadata = {
        "found": len(items),
        "returned": len(returned),
        "returned_chars": used_chars,
        "truncated": len(returned) < len(items),
        "strata": strata,
        "uncovered_strata": uncovered_strata,
        "coverage_unmet": coverage_unmet,
    }
    return returned, metadata


def build_index(
    repo_arg: str,
    queries: list[str],
    revision_arg: str | None,
    history_limit: int,
    include_name_similarity: bool = False,
    max_results: int = DEFAULT_MAX_RESULTS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict[str, Any]:
    if not queries or any(not query.strip() for query in queries):
        raise ValueError("at least one non-empty --query is required")
    if history_limit < 0:
        raise ValueError("--history-limit must be non-negative")
    if max_results <= 0:
        raise ValueError("--max-results must be positive")
    if max_chars <= 0:
        raise ValueError("--max-chars must be positive")
    repo = repository_root(Path(repo_arg).resolve())
    revision = validate_revision(repo, revision_arg)
    source_revision = revision or run_git(repo, ["rev-parse", "HEAD"]).stdout.strip()
    normalized_queries = sorted(set(query.strip() for query in queries))
    exact, events = collect_exact(repo, normalized_queries, revision)
    seed_paths = sorted(set(item["path"] for item in exact))
    raw_categories = {
        "exact_matches": exact,
        "event_evidence": events,
        "historical_cochange": historical_cochange(repo, seed_paths, revision, history_limit),
        "name_similarity": (
            name_similarity(tracked_paths(repo, revision), normalized_queries, set(seed_paths))
            if include_name_similarity else []
        ),
    }
    limited_categories: dict[str, list[dict[str, Any]]] = {}
    category_counts: dict[str, dict[str, Any]] = {}
    for category in EVIDENCE_CATEGORIES:
        limited_categories[category], category_counts[category] = limit_category(
            category,
            raw_categories[category],
            max_results,
            max_chars,
        )
    enabled_categories = ["exact_matches", "event_evidence"]
    if history_limit > 0:
        enabled_categories.append("historical_cochange")
    if include_name_similarity:
        enabled_categories.append("name_similarity")
    truncated = any(category_counts[category]["truncated"] for category in enabled_categories)
    uncovered_strata = {
        category: category_counts[category]["uncovered_strata"]
        for category in enabled_categories
        if category_counts[category]["uncovered_strata"]
    }
    coverage_unmet = any(category_counts[category]["coverage_unmet"] for category in enabled_categories)
    return {
        "schema_version": 2,
        "repository": ".",
        "revision": revision or "WORKTREE",
        "queries": normalized_queries,
        **limited_categories,
        "truncated": truncated,
        "uncovered_strata": uncovered_strata,
        "coverage_unmet": coverage_unmet,
        "run_metadata": {
            "repository_identity": ".",
            "source_revision": source_revision,
            "source_mode": "revision" if revision else "working_tree",
            "evidence_categories": enabled_categories,
            "history_limit": history_limit,
            "include_name_similarity": include_name_similarity,
            "limits": {
                "scope": "per_category",
                "max_results": max_results,
                "max_chars": max_chars,
            },
            "category_counts": category_counts,
            "truncated": truncated,
            "uncovered_strata": uncovered_strata,
            "coverage_unmet": coverage_unmet,
        },
        "limitations": [
            "Static search cannot prove that dynamic callers or subscribers do not exist.",
            "Historical co-change is an investigation lead, not proof of responsibility or dependency.",
            "Name similarity is low confidence and must not block a change or confirm a relationship.",
            "Result and character limits apply per evidence category; truncated output is incomplete and coverage_unmet identifies query/role/path coverage gaps.",
        ],
        "no_match_interpretation": "No exact match means only that the listed queries were not found by git grep at the listed revision.",
    }


def render_text(index: dict[str, Any]) -> str:
    lines = [
        f"revision: {index['revision']}",
        f"queries: {', '.join(index['queries'])}",
        f"truncated: {str(index['truncated']).lower()}",
        f"run_metadata: {json.dumps(index['run_metadata'], ensure_ascii=False, sort_keys=True)}",
    ]
    for category in EVIDENCE_CATEGORIES:
        lines.append(f"\n[{category}]")
        for item in index[category]:
            lines.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
    lines.append("\n[limitations]")
    lines.extend(f"- {item}" for item in index["limitations"])
    lines.append(f"- {index['no_match_interpretation']}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="path inside the Git repository")
    parser.add_argument("--rev", help="commit to index; defaults to the working tree")
    parser.add_argument("--query", action="append", required=True, help="exact symbol, key, event, or literal; repeatable")
    parser.add_argument("--history-limit", type=int, default=0, help="maximum relevant commits to inspect; 0 disables co-change")
    parser.add_argument("--include-name-similarity", action="store_true", help="include low-confidence path-name leads")
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS, help="maximum results per evidence category")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="maximum serialized result characters per evidence category")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        index = build_index(
            args.repo,
            args.query,
            args.rev,
            args.history_limit,
            args.include_name_similarity,
            args.max_results,
            args.max_chars,
        )
    except (GitError, ValueError) as error:
        print(f"source_index: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(index))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
