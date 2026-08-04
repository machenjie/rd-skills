from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-capabilities.py"
BUILD_SCRIPT = ROOT / "scripts" / "build.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("validate_capabilities_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_build_module():
    spec = importlib.util.spec_from_file_location(
        "validate_capabilities_build_test",
        BUILD_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateCapabilitiesSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.build = _load_build_module()

    def _fixture(self, root: Path, extra_rule: str = "") -> tuple[Path, Path]:
        skills_root = root / "src/foundation/capabilities"
        skill = skills_root / "example-capability" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            """---
name: example-capability
description: "Use with task-agent for an example decision; do not use without the named trigger or as the primary task owner."
---

# example-capability

## Registry Trigger

**Use when**

- example trigger

**Do not use when**

- example anti-trigger

## Skill Role

Bound the example decision to its named invariant and current source evidence.

## High-Value Rules

- Preserve the cache consistency invariant and choose invalidation from current source evidence.
- Bind cache-key ownership to the data owner before selecting invalidation.
- Derive eviction behavior from stale-read tolerance and measured writes.
"""
            + extra_rule
            + """

## Anti-Patterns

- A context-free default can violate the current system's contract.

## Stop Conditions

- Stop when cache ownership or stale-read tolerance is unknown.

## Targeted References

- No separate Reference is indexed; use this root decision contract.
""",
            encoding="utf-8",
        )
        registry = root / "src/registry/foundation-skills.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text(
            """foundation_skills:
  - name: example-capability
    path: src/foundation/capabilities/example-capability
    role_support:
      - task-agent
    trigger_signals:
      - example trigger
    anti_trigger_signals:
      - example anti-trigger
    reference_index: []
""",
            encoding="utf-8",
        )
        return skills_root, registry

    def _run(self, root: Path, skills_root: Path, registry: Path) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.multiple(
            self.module,
            ROOT=root,
            SKILLS_ROOT=skills_root,
            REGISTRY=registry,
            EXPECTED_FOUNDATION_CAPABILITY_COUNT=1,
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = self.module.main()
        return result, output.getvalue()

    def _root_use_triggers(self, skill_file: Path) -> list[str]:
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        section = self.module._section(body, "Registry Trigger")
        use_block = section.split("**Use when**", 1)[1].split(
            "**Do not use when**",
            1,
        )[0]
        values: list[str] = []
        for line in use_block.splitlines():
            if line.startswith("- "):
                values.append(" ".join(line[2:].split()))
            elif line[:1].isspace() and line.strip() and values:
                values[-1] += " " + " ".join(line.split())
        return values

    def _root_do_not_use_triggers(self, skill_file: Path) -> list[str]:
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        section = self.module._section(body, "Registry Trigger")
        block = section.split("**Do not use when**", 1)[1]
        values: list[str] = []
        for line in block.splitlines():
            if line.startswith("- "):
                values.append(" ".join(line[2:].split()))
            elif line[:1].isspace() and line.strip() and values:
                values[-1] += " " + " ".join(line.split())
        return values

    def _foundation_entry(self, name: str) -> dict[str, object]:
        entries = self.module.load_yaml_file(self.module.REGISTRY)[
            "foundation_skills"
        ]
        return next(entry for entry in entries if entry["name"] == name)

    def _compiled_foundation_projection(
        self,
        name: str,
        entry: dict[str, object],
    ) -> tuple[str, str]:
        skill_dir = self.module.SKILLS_ROOT / name
        metadata, _raw, body = self.module.parse_frontmatter(skill_dir / "SKILL.md")
        item = self.build.SkillItem(
            name=name,
            path=skill_dir,
            layer="foundation",
            description=str(metadata["description"]),
            metadata=metadata,
            body=body,
            registry=entry,
        )
        return body, self.build._render_layer3_reference(item)

    def test_senior_judgment_fallback_requires_no_narrower_owner(self) -> None:
        name = "senior-programming-judgment-core"
        skill_file = self.module.SKILLS_ROOT / name / "SKILL.md"
        metadata, _raw, _body = self.module.parse_frontmatter(skill_file)
        entry = self._foundation_entry(name)
        root_triggers = self._root_use_triggers(skill_file)
        root_anti_triggers = self._root_do_not_use_triggers(skill_file)

        self.assertEqual(entry["trigger_signals"], root_triggers)
        self.assertEqual(entry["anti_trigger_signals"], root_anti_triggers)
        self.assertTrue(
            all(
                trigger.startswith("no narrower capability owns")
                for trigger in root_triggers
            )
        )
        self.assertIn(
            "a narrower capability owns the task-local decision",
            root_anti_triggers,
        )
        self.assertIn(
            "only when no narrower capability owns it",
            metadata["description"],
        )

    def test_client_lifecycle_anti_triggers_are_closed_and_admission_safe(
        self,
    ) -> None:
        name = "client-lifecycle-state-restoration"
        skill_file = self.module.SKILLS_ROOT / name / "SKILL.md"
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        entry = self._foundation_entry(name)
        expected = [
            "no lifecycle or restoration decision",
            "only offline-sync policy",
            "one platform API without a shared state rule",
        ]
        old_combined = (
            "no lifecycle or restoration decision or only offline-sync policy "
            "or one platform API without a shared state rule"
        )

        def normalize(value: str) -> str:
            return " ".join(value.rstrip(".;").casefold().split())

        root_values = [
            normalize(value)
            for value in self._root_do_not_use_triggers(skill_file)
        ]
        registry_values = entry["anti_trigger_signals"]
        self.assertEqual([normalize(value) for value in expected], root_values)
        self.assertEqual(expected, registry_values)
        self.assertNotIn(normalize(old_combined), root_values)
        self.assertNotIn(old_combined, registry_values)
        self.assertNotIn(
            "shared cross-client restoration contract",
            " ".join(registry_values),
        )
        self.assertIn("shared cross-client restoration contract", body)
        self.assertIn("not a platform callback", body)
        _source_body, projected = self._compiled_foundation_projection(
            name,
            entry,
        )
        projected_normalized = projected.casefold()
        self.assertNotIn("## Registry Trigger", projected)
        self.assertNotIn(old_combined, projected_normalized)
        self.assertIn(
            "shared cross-client restoration contract",
            projected_normalized,
        )

        for rejected in (
            [old_combined],
            [
                *expected[:2],
                "one platform callback without a shared lifecycle state rule",
            ],
        ):
            with self.subTest(rejected=rejected):
                self.assertIn(
                    "ordered Root/Registry trigger scalars differ",
                    self._trigger_mirror_errors(root_values, rejected),
                )
                self.assertNotEqual(expected, rejected)

        admission = self.module.load_yaml_file(
            self.module.ROOT
            / "evals"
            / "capability-coverage"
            / "admission-cases.yaml"
        )["cases"]
        client_negatives = {
            row["case_kind"]: row["expected"]
            for row in admission
            if row.get("skill") == name and row.get("expected", {}).get(
                "selected"
            ) is False
        }
        self.assertEqual(
            {
                "simple": {
                    "selected": False,
                    "primary_skill": "installed-client-change-builder",
                },
                "adjacent": {
                    "selected": False,
                    "primary_skill": "installed-client-change-builder",
                },
                "domain-owned": {
                    "selected": False,
                    "primary_skill": "engineering-change-analysis",
                },
            },
            client_negatives,
        )

    def test_unit_testing_keeps_regression_evidence_conditional(self) -> None:
        name = "unit-testing"
        skill_file = self.module.SKILLS_ROOT / name / "SKILL.md"
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        entry = self._foundation_entry(name)
        output = self.module._section(body, "Output Contract")
        checklist = (
            skill_file.parent / "references/checklist.md"
        ).read_text(encoding="utf-8")
        evidence_patterns = (
            skill_file.parent / "references/evidence-patterns.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            [
                "unit behavior proof with changed local behavior or invariant, "
                "observable and denied outcomes, deterministic seams, "
                "double-fidelity limits, proportionate assertion challenge, "
                "cleanup evidence, and explicit proof boundary"
            ],
            entry["output_contract"],
        )
        self.assertNotIn("regression mechanism", output.casefold())
        self.assertIn("accepted defect, incident, or review finding", body)
        self.assertIn(
            "red-before-fix only for selected regression work",
            checklist,
        )
        self.assertIn("Selected regression mechanism is locked", evidence_patterns)
        self.assertNotIn(
            "Block closure when the test misses the reported mechanism",
            evidence_patterns,
        )

    @staticmethod
    def _trigger_mirror_errors(
        root_values: list[str],
        registry_values: list[str],
    ) -> list[str]:
        errors: list[str] = []
        if root_values != registry_values:
            errors.append("ordered Root/Registry trigger scalars differ")
        if len(registry_values) != len(set(registry_values)):
            errors.append("Registry trigger scalars must remain unique")
        return errors

    def test_five_section_core_passes_without_optional_scaffolding(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)

    def test_current_foundation_roots_meet_readability_and_sentence_limits(
        self,
    ) -> None:
        tighten: list[dict[str, object]] = []
        compound: list[dict[str, object]] = []
        over_sentence_limit: list[dict[str, object]] = []
        for skill_file in sorted(self.module.SKILLS_ROOT.glob("*/SKILL.md")):
            source = skill_file.read_text(encoding="utf-8")
            _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
            findings = self.module.ai_readability_findings(
                source,
                str(skill_file.relative_to(self.module.ROOT)),
            )
            tighten.extend(
                finding for finding in findings if finding.get("band") == "tighten"
            )
            compound.extend(
                finding
                for finding in findings
                if finding.get("kind") == "bullet-decisions"
            )
            over_sentence_limit.extend(
                {
                    "path": str(skill_file.relative_to(self.module.ROOT)),
                    **item,
                }
                for item in self.module.ai_markdown_list_sentence_counts(
                    self.module._section(body, "High-Value Rules")
                )
                if int(item["sentences"]) > 2
            )
        self.assertEqual([], tighten)
        self.assertEqual([], compound)
        self.assertEqual([], over_sentence_limit)

    def test_current_readability_tightenings_keep_independent_decisions(self) -> None:
        def bullets(name: str, section: str) -> list[str]:
            _metadata, _raw, body = self.module.parse_frontmatter(
                self.module.SKILLS_ROOT / name / "SKILL.md"
            )
            return [
                line[2:]
                for line in self.module._section(body, section).splitlines()
                if line.startswith("- ")
            ]

        language = bullets("language-runtime-selection", "High-Value Rules")
        language_boundary = (
            "Define deployment, migration, rollback, and exit behavior plus any "
            "ABI/FFI, generated-contract, mixed-runtime-observability, or "
            "coexistence obligations the choice actually creates."
        )
        self.assertEqual(
            [
                language_boundary,
                "Record versions, environment, sample, date, and unproved limits "
                "for benchmark and support claims.",
            ],
            language[
                language.index(language_boundary) : language.index(language_boundary) + 2
            ],
        )

        observability = bullets("observability", "High-Value Rules")
        alert_boundary = "Give alerts a condition, owner, severity, and response."
        self.assertEqual(
            [
                alert_boundary,
                "Define or adjust an SLI/SLO only for an existing objective or "
                "triggered risk, and prove its semantics.",
            ],
            observability[
                observability.index(alert_boundary) : observability.index(alert_boundary)
                + 2
            ],
        )

        shell = bullets("shell-cli-professional-usage", "Anti-Patterns")
        destructive_boundary = (
            "An empty, relative, symlinked, or environment-derived destructive "
            "target can bypass a superficial string check."
        )
        self.assertEqual(
            [
                destructive_boundary,
                "Cleanup traps can overwrite the command's real exit status.",
            ],
            shell[
                shell.index(destructive_boundary) : shell.index(destructive_boundary) + 2
            ],
        )

    def test_solution_optimality_routes_stack_commitments_in_all_consumers(
        self,
    ) -> None:
        name = "solution-optimality-evaluation"
        route = (
            "The open decision is a technology-stack commitment involving a "
            "framework, platform, datastore, infrastructure component, or managed "
            "service; use `technology-stack-selection`."
        )
        projected_route = (
            "Route technology-stack commitments involving a framework, platform, "
            "datastore, infrastructure component, or managed service to "
            "`technology-stack-selection`."
        )
        entry = self._foundation_entry(name)
        body, projected = self._compiled_foundation_projection(name, entry)
        root_routes = self._root_do_not_use_triggers(
            self.module.SKILLS_ROOT / name / "SKILL.md"
        )

        self.assertIn(route, root_routes)
        self.assertIn(
            route.replace("`", "").removesuffix("."),
            entry["anti_trigger_signals"],
        )
        self.assertIn(projected_route, projected)
        self.assertIn("technology-stack-selection", body)
        self.assertIn("technology-stack-selection", projected)

        rules = [
            line[2:]
            for line in self.module._section(body, "High-Value Rules").splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(8, len(rules))
        self.assertIn(
            "Record plausible omissions from discriminating resource and maintenance "
            "comparisons as decision limits.",
            rules,
        )
        self.assertIn(
            "Require performance claims to identify workload, expected and worst "
            "cases, budget, environment, and measurement limits.",
            rules,
        )

        output_section = self.module._section(body, "Output Contract")
        output_fields, output_errors = self.module._output_contract_items(output_section)
        self.assertEqual([], output_errors)
        self.assertEqual(entry["output_contract"], output_fields)
        self.assertEqual(1, len(entry["output_contract"]))
        self.assertNotIn("## Output Contract", projected)
        self.assertNotIn(entry["output_contract"][0], projected)

    def test_targeted_validation_command_entry_boundary(self) -> None:
        skill_dir = self.module.SKILLS_ROOT / "targeted-validation-selection"
        entry = self._foundation_entry("targeted-validation-selection")
        body, projected = self._compiled_foundation_projection(
            "targeted-validation-selection",
            entry,
        )
        do_not_use = self._root_do_not_use_triggers(
            skill_dir / "SKILL.md"
        )
        checklist = (
            skill_dir / "references" / "repository-command-entry-evidence.md"
        ).read_text(encoding="utf-8")
        combined = body + "\n" + checklist

        self.assertEqual(
            [
                "accepted proof strategy and observable acceptance",
                "changed paths and material risk surfaces",
                "repository guidance command definitions and existing tests",
                "command targets mutation surfaces hooks/subprocesses credentials "
                "external effects authority recovery cleanup and retained-output "
                "constraints",
                "available command results and freshness input/hash/time facts",
            ],
            entry["required_inputs"],
        )
        self.assertEqual(
            [
                "`quality-test-gate` has not defined proof strategy and observable "
                "acceptance;",
                "exact commands and their acceptance and risk coverage are already "
                "established.",
            ],
            do_not_use,
        )
        self.assertEqual(
            [
                "quality-test-gate has not defined proof strategy and observable "
                "acceptance",
                "exact commands and their acceptance and risk coverage are already "
                "established",
            ],
            entry["anti_trigger_signals"],
        )
        for required in (
            "test/build/schema/lint/static/generator entrypoints",
            "existing tests",
            "command coverage",
            "expected signal",
            "mutation surfaces",
            "retained-output boundary",
            "actual result when run",
            "freshness input/hash/time facts",
            "unavailable-entry fallback",
            "unverified scope",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

        for forbidden in (
            "active profile",
            "task contract",
            "workspace-writing",
            "non-modifying",
            "execution/authority verdict",
            "last material edit",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined.casefold())

        rules = [
            line[2:]
            for line in self.module._section(body, "High-Value Rules").splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(8, len(rules))
        self.assertEqual(
            [
                "Inspect repository guidance and command definitions for "
                "test/build/schema/lint/static/generator entrypoints.",
                "When entrypoint coverage is disputed, use existing tests to "
                "establish the behavior and paths covered by candidate entrypoints.",
                "For the accepted proof strategy, map its observable acceptance and "
                "material risk surfaces to command coverage and repository sources.",
                "Select exact smallest-sufficient commands with combined coverage "
                "for the accepted mapping and a defined expected signal per command.",
                "Run a selected command only after resolving its target, working "
                "directory, hooks/subprocesses, mutation surfaces, credentials, "
                "external effects, authority, stop condition, recovery, cleanup, and "
                "retained-output boundary.",
                "Record freshness input/hash/time facts without deciding evidence "
                "timing.",
                "Select an unavailable-entry fallback only from repository-defined "
                "commands with evidenced coverage.",
                "Preserve unverified scope, proof limits, and residual risk when "
                "coverage remains incomplete.",
            ],
            rules,
        )
        self.assertEqual(
            "Inspect repository guidance and command definitions for "
            "test/build/schema/lint/static/generator entrypoints.",
            rules[0],
        )
        self.assertEqual(
            "Preserve unverified scope, proof limits, and residual risk when coverage "
            "remains incomplete.",
            rules[-1],
        )
        self.assertNotIn("## Execution Checklist", body)

        output_section = self.module._section(body, "Output Contract")
        output_fields, output_errors = self.module._output_contract_items(output_section)
        self.assertEqual([], output_errors)
        self.assertEqual(
            [
                "Repository-entrypoint inspection evidence covering "
                "test/build/schema/lint/static/generator entrypoints and existing tests.",
                "Record exact smallest-sufficient commands.",
                "Map observable-acceptance and risk-surface coverage per command.",
                "Record the expected signal.",
                "Record command target, working directory, mutation/external-effect "
                "classification, credentials/authority, stop condition, recovery, "
                "cleanup, and retained-output boundary before execution.",
                "Record the actual result when run.",
                "Record freshness input/hash/time facts.",
                "Record the unavailable-entry fallback.",
                "State unverified scope, proof limits, and residual risk.",
            ],
            output_fields,
        )
        self.assertEqual(output_fields, entry["output_contract"])
        self.assertNotIn("## Output Contract", projected)

    def test_tighten_sentence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            long_rule = "- Preserve " + " ".join(
                f"word{index}" for index in range(32)
            ) + "."
            skill.write_text(
                source.replace(
                    "- Preserve the cache consistency invariant and choose invalidation from current source evidence.",
                    long_rule,
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("Foundation root sentence requires tightening", output)

    def test_compound_bullet_remains_human_review_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "- Preserve the cache consistency invariant and choose invalidation from current source evidence.",
                    "- Bind cache keys to the data owner. Reject invalidation from a weaker boundary.",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)
        findings = self.module.ai_readability_findings(
            "- Bind cache keys to the data owner. Reject invalidation from a weaker boundary.",
            "fixture",
        )
        self.assertTrue(
            any(finding.get("kind") == "bullet-decisions" for finding in findings)
        )

    def test_high_value_rule_over_two_sentences_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "- Preserve the cache consistency invariant and choose invalidation from current source evidence.",
                    "- Preserve the named invariant. Current proof remains scoped. "
                    "Residual risk remains explicit.",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("exceeds the two-sentence limit", output)

    def test_rewritten_registry_triggers_preserve_exact_mirror_and_or_order(
        self,
    ) -> None:
        cases = {
            "architecture-enforcement-tooling": (
                0,
                1,
                "architecture enforcement tooling, import boundary check, cycle detection, public private export, forbidden dependency lint, type strictness, dead code, complexity threshold, generated code exclusion, CI, ArchUnit, Dependency Cruiser, import linter, eslint boundaries, go vet, staticcheck",
            ),
            "build-tool-professional-usage": (
                1,
                2,
                "undeclared dependency, generated source, generated source declaration, generator output source of truth, reproducible artifact, checksum, digest, build cache, action key, toolchain pin, local CI mismatch, make parallel, phony target, order-only dependency, bazel sandbox, classpath, sourcepath, output directory",
            ),
            "data-side-effect-flow-tracing": (
                0,
                1,
                "data side effect flow, input validation, mapping, policy, mutation, transaction, persistence, cache, event, external IO, logging, metrics, file IO, clock, random, env, outbox, publish after commit, idempotency, compensation, hidden side effect, mapper, getter",
            ),
            "git-professional-usage": (
                1,
                2,
                "generated-output, source-authority, ours, theirs, merge-base, conflict-marker, unrelated-staged-changes, unstaged-diff, staged-diff, user-changes, overwrite, rollback, ref, protected-branch, history-rewrite, backup-branch, branch-naming, commit-message, commit-splitting, bisect, failure-isolation",
            ),
            "language-performance-safety": (
                1,
                2,
                "CPU-bound, storage IO, network IO, file IO, blocking IO, non-blocking IO, coroutine, goroutine, thread pool, worker pool, lock held across IO, event-loop blocking, unbounded fan-out, pool sizing, per-operation client construction, response body leak, object allocation regression, design pattern performance risk",
            ),
        }
        entries = {
            entry["name"]: entry
            for entry in self.module.load_yaml_file(self.module.REGISTRY)[
                "foundation_skills"
            ]
        }
        network_triggers = [
            "Nginx Envoy HAProxy Cloudflare Fastly CloudFront ALB NLB",
            "ingress API gateway service mesh WAF CDN reverse proxy load balancer",
            "TLS DNS SNI ALPN",
            "HTTP proxy header X-Forwarded-For Forwarded Host CORS",
            "WebSocket SSE gRPC timeout-chain",
            "502 503 504 retry-amplification upstream-status edge origin trace context",
            "path-rewrite cache-key TTL invalidation purge stale-behavior per-user data health check origin shielding",
        ]
        self.assertEqual(
            network_triggers,
            entries["network-protocol-gateway-usage"]["trigger_signals"],
        )
        self.assertEqual(
            network_triggers,
            self._root_use_triggers(
                self.module.SKILLS_ROOT
                / "network-protocol-gateway-usage"
                / "SKILL.md"
            ),
        )
        for name, (target_index, expected_count, target) in cases.items():
            with self.subTest(name=name):
                registry_values = entries[name]["trigger_signals"]
                root_values = self._root_use_triggers(
                    self.module.SKILLS_ROOT / name / "SKILL.md"
                )
                self.assertEqual([], self._trigger_mirror_errors(
                    root_values,
                    registry_values,
                ))
                self.assertEqual(expected_count, len(registry_values))
                self.assertEqual(target, registry_values[target_index])
                self.assertEqual(1, registry_values.count(target))

                missing = [value for value in registry_values if value != target]
                self.assertIn(
                    "ordered Root/Registry trigger scalars differ",
                    self._trigger_mirror_errors(root_values, missing),
                )
                if len(registry_values) > 1:
                    reordered = list(reversed(registry_values))
                    merged = [" ".join(registry_values)]
                    self.assertIn(
                        "ordered Root/Registry trigger scalars differ",
                        self._trigger_mirror_errors(root_values, reordered),
                    )
                    self.assertIn(
                        "ordered Root/Registry trigger scalars differ",
                        self._trigger_mirror_errors(root_values, merged),
                    )

    def test_exact_generic_scaffold_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(
                root,
                "\n- State source evidence, what the decision proves, what remains unverified, and the next owner.",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("forbidden generic scaffold line", output)

    def test_required_section_order_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            rules_start = source.index("## High-Value Rules")
            anti_start = source.index("## Anti-Patterns")
            refs_start = source.index("## Targeted References")
            skill.write_text(
                source[:rules_start]
                + source[anti_start:refs_start]
                + source[rules_start:anti_start]
                + source[refs_start:],
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("must appear after", output)

    def test_decision_card_rejects_delayed_rules_hollow_rules_and_missing_stop(
        self,
    ) -> None:
        mutations = {
            "delayed": (
                "## High-Value Rules",
                ("Decision context remains non-operative.\n" * 45)
                + "\n## High-Value Rules",
                "High-Value Rules must begin within",
            ),
            "hollow": (
                "- Preserve the cache consistency invariant and choose invalidation from current source evidence.\n"
                "- Bind cache-key ownership to the data owner before selecting invalidation.\n"
                "- Derive eviction behavior from stale-read tolerance and measured writes.",
                "- First inspect the current decision and verify current evidence.\n"
                "- Preserve the named invariant using the selected boundary.\n"
                "- Return the decision with proof limits and residual risk.",
                "decision density",
            ),
            "missing-stop": (
                "## Stop Conditions\n\n"
                "- Stop when cache ownership or stale-read tolerance is unknown.\n\n",
                "",
                "Stop Conditions must be present",
            ),
        }
        for label, (old, new, expected) in mutations.items():
            with self.subTest(variant=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                skills_root, registry = self._fixture(root)
                skill = skills_root / "example-capability/SKILL.md"
                skill.write_text(
                    skill.read_text(encoding="utf-8").replace(old, new),
                    encoding="utf-8",
                )
                result, output = self._run(root, skills_root, registry)
                self.assertEqual(1, result)
                self.assertIn(expected, output)

    def test_decision_card_accepts_domain_numbered_rules_and_rejects_hollow_ones(
        self,
    ) -> None:
        unordered_continuation_rules = (
            "- Every lifecycle needs allowed and forbidden transitions, actors, guards,\n"
            "  and effective timing where relevant.\n"
            "- From that candidate, follow imports, calls, references, and tests\n"
            "  only as needed for cache invalidation.\n"
            "- Preserve retry semantics during concurrent cache invalidation."
        )
        numbered_continuation_rules = (
            "1. Every lifecycle needs allowed and forbidden transitions, actors, guards,\n"
            "   and effective timing where relevant.\n"
            "2. From that candidate, follow imports, calls, references, and tests\n"
            "   only as needed for cache invalidation.\n"
            "3. Preserve retry semantics during concurrent cache invalidation."
        )
        hollow_multiline_rules = (
            "1. First inspect the current decision\n"
            "   and verify current evidence.\n"
            "2. Preserve the named invariant\n"
            "   using the selected boundary.\n"
            "3. Return the decision with proof limits\n"
            "   and residual risk."
        )
        unindented_lending_rules = (
            "- Apply the named choice.\n"
            "Derive cache invalidation from the data owner before eviction.\n"
            "- Bind cache-key ownership to the data owner before selecting invalidation.\n"
            "- Derive eviction behavior from stale-read tolerance and measured writes."
        )
        blank_line_lending_rules = (
            "- Apply the named choice.\n\n"
            "  Derive cache invalidation from the data owner before eviction.\n"
            "- Bind cache-key ownership to the data owner before selecting invalidation.\n"
            "- Derive eviction behavior from stale-read tolerance and measured writes."
        )
        original = (
            "- Preserve the cache consistency invariant and choose invalidation from current source evidence.\n"
            "- Bind cache-key ownership to the data owner before selecting invalidation.\n"
            "- Derive eviction behavior from stale-read tolerance and measured writes."
        )
        for label, replacement, expected_result, non_list_content in (
            ("unordered-continuation", unordered_continuation_rules, 0, False),
            ("numbered-continuation", numbered_continuation_rules, 0, False),
            ("hollow-multiline", hollow_multiline_rules, 1, False),
            ("unindented-lending", unindented_lending_rules, 1, True),
            ("blank-line-lending", blank_line_lending_rules, 1, True),
        ):
            with self.subTest(variant=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                skills_root, registry = self._fixture(root)
                skill = skills_root / "example-capability/SKILL.md"
                skill.write_text(
                    skill.read_text(encoding="utf-8").replace(
                        original,
                        replacement,
                    ),
                    encoding="utf-8",
                )
                result, output = self._run(root, skills_root, registry)
                _metadata, _raw_frontmatter, body = self.module.parse_frontmatter(
                    skill,
                )
                shared = self.module.foundation_decision_card(body)
                self.assertEqual(expected_result, result, output)
                self.assertEqual(bool(expected_result), shared["applicable"])
                self.assertEqual(
                    non_list_content,
                    "non-list-content" in shared["findings"],
                )
                if expected_result:
                    self.assertIn("decision density", output)

    def test_nonempty_optional_section_passes_in_validated_position(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "## High-Value Rules",
                    "## Inputs\n\n- Current ownership and invariant evidence.\n\n## High-Value Rules",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)

    def test_output_contract_exactly_matching_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "## Targeted References",
                    "## Output Contract\n\n"
                    "- bounded decision with evidence, proof limits,\n"
                    "  and residual owner\n\n"
                    "## Targeted References",
                ),
                encoding="utf-8",
            )
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "    reference_index: []",
                    "    output_contract:\n"
                    "      - bounded decision with evidence, proof limits, and residual owner\n"
                    "    reference_index: []",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)

    def test_output_contract_drift_is_rejected_as_exact_bullet_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "## Targeted References",
                    "## Output Contract\n\n- narrower runtime decision\n\n"
                    "## Targeted References",
                ),
                encoding="utf-8",
            )
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "    reference_index: []",
                    "    output_contract:\n"
                    "      - stale broad report\n"
                    "    reference_index: []",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("Output Contract bullet-set must exactly match registry", output)

    def test_intentionally_omitted_output_contract_remains_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "    reference_index: []",
                    "    output_contract:\n"
                    "      - registry dispatch metadata remains available\n"
                    "    reference_index: []",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)

    def test_empty_required_section_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            start = source.index("## Anti-Patterns")
            end = source.index("## Targeted References")
            skill.write_text(
                source[:start] + "## Anti-Patterns\n\n<!-- empty -->\n\n" + source[end:],
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("empty heading 'Anti-Patterns'", output)

    def test_negative_boundary_does_not_substitute_for_positive_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace("**Use when**\n\n", ""),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("must contain a 'Use when' boundary", output)

    def test_required_core_heading_must_be_level_two(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "## Registry Trigger", "### Registry Trigger"
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("required Foundation section 'Registry Trigger' must be level 2", output)

    def test_indexed_reference_must_be_linked_from_targeted_references(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill_dir = skills_root / "example-capability"
            references = skill_dir / "references"
            references.mkdir()
            (references / "only.md").write_text("# Only\n", encoding="utf-8")
            skill = skill_dir / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Preserve the cache consistency invariant and choose invalidation from current source evidence.",
                    "- Preserve the named invariant; see references/only.md for detail.",
                ),
                encoding="utf-8",
            )
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "    reference_index: []",
                    "    reference_index:\n"
                    "      - path: references/only.md\n"
                    "        type: targeted\n"
                    "        load_when: the example capability task needs only-file guidance\n"
                    "        do_not_load_when: the task changes no behavior covered by only-file guidance\n"
                    "        required_by:\n"
                    "          - task-agent\n"
                    "        required_output:\n"
                    "          - decision-record",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("Targeted References must link references/only.md", output)

    def test_legacy_h2_is_rejected_without_requiring_profile_choreography(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            skill = skills_root / "example-capability/SKILL.md"
            source = skill.read_text(encoding="utf-8")
            skill.write_text(
                source.replace(
                    "## Targeted References",
                    "## Required Inputs\n\n- Legacy scaffold.\n\n## Targeted References",
                ),
                encoding="utf-8",
            )
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "      - task-agent\n    trigger_signals:",
                    "      - task-agent\n      - review-agent\n    trigger_signals:",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(1, result)
        self.assertIn("unsupported Foundation section(s): Required Inputs", output)
        self.assertNotIn("must name supported profile", output)

    def test_registry_role_support_does_not_require_profile_names_in_body(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root, registry = self._fixture(root)
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "      - task-agent\n    trigger_signals:",
                    "      - task-agent\n      - review-agent\n    trigger_signals:",
                ),
                encoding="utf-8",
            )
            result, output = self._run(root, skills_root, registry)
        self.assertEqual(0, result, output)


if __name__ == "__main__":
    unittest.main()
