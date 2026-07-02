#!/usr/bin/env python3
"""Validate productization docs, links, and release boundary assets."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "docs/QUICKSTART.md",
    "docs/BENCHMARKS.md",
    "docs/SCORECARD.md",
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
    "docs/COMPARISON.md",
    "docs/LICENSE_DECISION.md",
    "reports/README.md",
    "reports/professional-scorecard.md",
    "reports/professional-scorecard.json",
    "reports/executor-adapter-eval.md",
    "reports/executor-adapter-eval.json",
    "reports/activation-precision.md",
    "reports/activation-precision.json",
    "reports/runtime-telemetry-sample.json",
    "reports/hook-validation.md",
    "reports/hook-validation.json",
    "reports/installation-validation.md",
    "reports/installation-validation.json",
    "reports/public-benchmark-summary.md",
    "reports/public-benchmark-summary.json",
    "config/open-source-release.yaml",
    "schemas/marketplace-index.schema.json",
    "scripts/generate-professional-scorecard.py",
    "scripts/eval-executor-adapters.py",
    "scripts/eval-activation-precision.py",
    "scripts/generate-public-benchmark-summary.py",
    "scripts/generate-examples-showcase.py",
    "scripts/generate-marketplace-catalog.py",
    "scripts/render-scorecard-dashboard.py",
    "scripts/quickstart.py",
    "scripts/validate-docs-consistency.py",
    "scripts/validate-open-source-readiness.py",
    "scripts/export-marketplace-index.py",
    "scripts/validate-marketplace-index.py",
    "scripts/validate-examples.py",
)
DOC_LINK_FILES = (
    "README.md",
    "docs/QUICKSTART.md",
    "docs/BENCHMARKS.md",
    "docs/SCORECARD.md",
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
    "docs/COMPARISON.md",
    "docs/OPEN_SOURCE_READINESS.md",
    "docs/LICENSE_DECISION.md",
    "docs/RELEASE.md",
    "examples/README.md",
    "reports/README.md",
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _iter_local_links(path: Path) -> list[Path]:
    links: list[Path] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        links.append((path.parent / unquote(target)).resolve())
    return links


def validate_productization_assets(root: Path) -> list[str]:
    """Return validation errors for productization docs and local links."""
    errors: list[str] = []
    for required in REQUIRED_FILES:
        if not (root / required).is_file():
            errors.append(f"missing required productization asset: {required}")

    quickstart = root / "docs" / "QUICKSTART.md"
    if quickstart.exists():
        text = quickstart.read_text(encoding="utf-8")
        for term in ("recommended", "full", "dev", "doctor", "change-forge-router"):
            if term not in text:
                errors.append(f"docs/QUICKSTART.md missing required term: {term}")

    for rel_path in DOC_LINK_FILES:
        path = root / rel_path
        if not path.exists():
            continue
        for target in _iter_local_links(path):
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"{rel_path} links outside repository: {target}")
                continue
            if not target.exists():
                errors.append(f"{rel_path} has missing local link target: {target.relative_to(root)}")

    if (root / "src" / "toolbox").exists():
        errors.append("forbidden path exists: src/toolbox")
    if (root / "registry" / "toolbox.yaml").exists():
        errors.append("forbidden path exists: registry/toolbox.yaml")
    errors.extend(_docs_consistency_errors(root))
    return errors


def _docs_consistency_errors(root: Path) -> list[str]:
    script = root / "scripts" / "validate-docs-consistency.py"
    if not script.exists():
        return ["missing docs consistency validator: scripts/validate-docs-consistency.py"]
    spec = importlib.util.spec_from_file_location("validate_docs_consistency_for_productization", script)
    if spec is None or spec.loader is None:
        return ["unable to load docs consistency validator"]
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return [
        f"docs consistency: {error}"
        for error in module.validate_docs_consistency(root)
    ]


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for productization asset validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    errors = validate_productization_assets(Path(args.root))
    if errors:
        for error in errors:
            print(f"validate-productization-assets: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-productization-assets: validated productization docs and links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
