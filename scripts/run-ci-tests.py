#!/usr/bin/env python3
"""Project the Core-owned affected-unit-test contract into deterministic CI runs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from validation_utils import validate_core_contracts


ROOT = Path(__file__).resolve().parents[1]
CORE_RELATIVE_PATH = Path("src/control-model/core-contracts.json")
HEX_REVISION = re.compile(r"[0-9a-fA-F]{40}")


class SelectionError(RuntimeError):
    """The selector cannot safely construct a bounded unittest invocation."""


def _load_core(root: Path) -> dict[str, Any]:
    data = json.loads((root / CORE_RELATIVE_PATH).read_text(encoding="utf-8"))
    errors = validate_core_contracts(data)
    if errors:
        raise SelectionError("invalid Core CI contract: " + "; ".join(errors))
    return data


def _discover_modules(
    root: Path,
    relative_root: str,
    pattern: str,
) -> list[str]:
    base = root / relative_root
    modules = sorted(
        path.relative_to(root).as_posix()
        for path in base.rglob(pattern)
        if path.is_file()
    ) if base.is_dir() else []
    if not modules:
        raise SelectionError(
            f"full unittest discovery is empty under {relative_root!r} for {pattern!r}"
        )
    return modules


def _discover_full_suite_modules(root: Path, core: dict[str, Any]) -> list[str]:
    full_suite = core["ci_validation_contract"]["full_suite"]
    return _discover_modules(root, full_suite["root"], full_suite["pattern"])


def _stable_shards(modules: Sequence[str], shard_count: int) -> list[list[str]]:
    if shard_count != 2:
        raise ValueError("CI contract requires exactly 2 shards")
    if len(modules) != len(set(modules)):
        raise ValueError("duplicate test module in shard input")
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    for index, module in enumerate(sorted(modules)):
        shards[index % shard_count].append(module)
    return shards


def _run_git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _parse_name_status_z(payload: bytes) -> list[tuple[str, str]]:
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", "strict")
        index += 1
        if not status:
            raise SelectionError("git diff returned an empty status")
        kind = status[0]
        if kind in {"R", "C"}:
            if index + 1 >= len(fields):
                raise SelectionError("git diff returned a truncated rename or copy")
            old_path = fields[index].decode("utf-8", "surrogateescape")
            new_path = fields[index + 1].decode("utf-8", "surrogateescape")
            entries.extend([("D", old_path), ("A", new_path)])
            index += 2
            continue
        if index >= len(fields):
            raise SelectionError("git diff returned a status without a path")
        path = fields[index].decode("utf-8", "surrogateescape")
        entries.append((kind, path))
        index += 1
    return entries


def _matches(path: str, pattern: str) -> bool:
    if pattern == "tests/**/test*.py":
        candidate = PurePosixPath(path)
        return (
            len(candidate.parts) >= 2
            and candidate.parts[0] == "tests"
            and candidate.name.startswith("test")
            and candidate.suffix == ".py"
        )
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path.startswith(prefix + "/")
    return fnmatchcase(path, pattern)


def _fallback_selection(
    root: Path,
    core: dict[str, Any],
    *,
    base_sha: str | None,
    head_sha: str | None,
    reason: str,
    decisions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    modules = _discover_full_suite_modules(root, core)
    return {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "fallback": True,
        "fallback_reason": reason,
        "changed_paths": decisions or [],
        "selected_test_modules": modules,
        "shards": _stable_shards(
            modules, core["ci_validation_contract"]["shard_count"]
        ),
    }


def _safe_changed_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    return bool(
        path
        and "\x00" not in path
        and "\\" not in path
        and not candidate.is_absolute()
        and ".." not in candidate.parts
    )


def _selection_from_entries(
    root: Path,
    core: dict[str, Any],
    entries: Sequence[tuple[str, str]],
    *,
    base_sha: str,
    head_sha: str,
) -> dict[str, Any]:
    contract = core["ci_validation_contract"]
    if not entries:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="empty-diff",
        )
    selected: set[str] = set()
    decisions: list[dict[str, Any]] = []
    fallback_reason: str | None = None
    for status, path in entries:
        mapping_ids: list[str] = []
        producer_ids: set[str] = set()
        test_modules: set[str] = set()
        coverage: set[str] = set()
        reason = ""
        if not _safe_changed_path(path):
            fallback_reason = fallback_reason or "unsafe-path"
            reason = "unsafe repository-relative path; use the full suite"
        elif status == "D":
            fallback_reason = fallback_reason or "deleted-path"
            reason = "deleted paths fail closed because their former owner may be absent"
        elif status not in {"A", "M"}:
            fallback_reason = fallback_reason or "unsupported-status"
            reason = f"unsupported git status {status!r}; use the full suite"
        else:
            for pattern in contract["test_self_patterns"]:
                if _matches(path, pattern):
                    mapping_ids.append("changed-test-self")
                    test_modules.add(path)
                    coverage.add("unit-tests")
            for mapping in contract["mappings"]:
                if any(_matches(path, pattern) for pattern in mapping["path_patterns"]):
                    mapping_ids.append(mapping["id"])
                    producer_ids.update(mapping["producer_ids"])
                    test_modules.update(mapping["test_modules"])
                    coverage.add(mapping["coverage"])
            if not mapping_ids:
                fallback_reason = fallback_reason or "unmatched-path"
                reason = "no Core-owned affected-test mapping; use the full suite"
            else:
                selected.update(test_modules)
                reason = "union of changed-test self-selection and Core-owned mappings"
        decisions.append(
            {
                "status": status,
                "path": path,
                "mapping_ids": sorted(mapping_ids),
                "producer_ids": sorted(producer_ids),
                "test_modules": sorted(test_modules),
                "coverage": sorted(coverage),
                "selected": bool(mapping_ids),
                "rationale": reason,
            }
        )
    if fallback_reason is not None:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason=fallback_reason,
            decisions=decisions,
        )
    if not selected:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="empty-selection",
            decisions=decisions,
        )
    modules = sorted(selected)
    return {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "fallback": False,
        "fallback_reason": None,
        "changed_paths": decisions,
        "selected_test_modules": modules,
        "shards": _stable_shards(modules, contract["shard_count"]),
    }


def _valid_revision(revision: str | None) -> bool:
    return bool(revision and HEX_REVISION.fullmatch(revision))


def select(
    root: Path,
    core: dict[str, Any],
    base_sha: str | None,
    head_sha: str | None,
) -> dict[str, Any]:
    if not base_sha or not head_sha:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="missing-revision",
        )
    if not _valid_revision(base_sha) or not _valid_revision(head_sha):
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="invalid-revision",
        )
    if base_sha == "0" * 40 or head_sha == "0" * 40:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="zero-revision",
        )
    for revision in (base_sha, head_sha):
        exists = _run_git(root, ["cat-file", "-e", f"{revision}^{{commit}}"])
        if exists.returncode != 0:
            return _fallback_selection(
                root,
                core,
                base_sha=base_sha,
                head_sha=head_sha,
                reason="nonexistent-revision",
            )
    changed = _run_git(
        root,
        ["diff", "--name-status", "-z", "--no-ext-diff", "--no-textconv", base_sha, head_sha],
    )
    if changed.returncode != 0:
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="git-diff-failed",
        )
    try:
        entries = _parse_name_status_z(changed.stdout)
    except (SelectionError, UnicodeError):
        return _fallback_selection(
            root,
            core,
            base_sha=base_sha,
            head_sha=head_sha,
            reason="malformed-diff",
        )
    return _selection_from_entries(
        root,
        core,
        entries,
        base_sha=base_sha,
        head_sha=head_sha,
    )


def _exec_unittest(
    root: Path,
    core: dict[str, Any],
    modules: Sequence[str],
) -> None:
    del core
    if not modules or len(modules) != len(set(modules)):
        raise SelectionError("unittest selection must be non-empty and duplicate-free")
    os.chdir(root)
    os.execv(sys.executable, [sys.executable, "-m", "unittest", *modules])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("explain", "list", "shards", "run"))
    parser.add_argument("--base", default=os.environ.get("CI_BASE_SHA"))
    parser.add_argument("--head", default=os.environ.get("CI_HEAD_SHA"))
    parser.add_argument("--shard", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        core = _load_core(ROOT)
        result = select(ROOT, core, args.base, args.head)
        if args.action == "explain":
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.action == "list":
            print("\n".join(result["selected_test_modules"]))
            return 0
        if args.action == "shards":
            print(json.dumps(result["shards"], indent=2))
            return 0
        if args.shard is None or not 0 <= args.shard < len(result["shards"]):
            raise SelectionError("run requires --shard 0 or --shard 1")
        print(
            json.dumps(
                {
                    "fallback": result["fallback"],
                    "fallback_reason": result["fallback_reason"],
                    "shard": args.shard,
                    "test_modules": result["shards"][args.shard],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        _exec_unittest(ROOT, core, result["shards"][args.shard])
    except (OSError, SelectionError, ValueError, json.JSONDecodeError) as exc:
        print(f"CI test selection failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
