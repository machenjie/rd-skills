from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-professional-routing-coverage.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_professional_routing_coverage", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateProfessionalRoutingCoverageTests(unittest.TestCase):
    def test_expected_route_overlap_alone_is_not_covered(self) -> None:
        module = _load_module()
        case = module.RoutingCase(
            case_id="low-level-rust-ffi-memory-safety",
            path="evals/routing/low-level-rust-ffi-memory-safety.yaml",
            text="Rust FFI pointer lifetime issue with selected backend-change-builder and regression-testing.",
            risk_text="Rust FFI pointer lifetime issue.",
            skills=["backend-change-builder"],
            capabilities=["regression-testing"],
            risk_triggers=["ffi", "memory safety"],
        )

        self.assertFalse(
            module._benchmark_route_matches_expected(
                "IDOR from missing object ownership check",
                ["backend-change-builder"],
                ["regression-testing"],
                case,
            )
        )
        self.assertEqual(
            module._risk_match_strength("IDOR from missing object ownership check", case),
            "none",
        )

    def test_normalized_core_phrase_counts_as_strong_match(self) -> None:
        module = _load_module()
        case = module.RoutingCase(
            case_id="backend-idor-tenant-leak-hidden-risk",
            path="evals/routing/backend-idor-tenant-leak-hidden-risk.yaml",
            text="Fix invoice endpoint with tenant leak and object-level permission risk.",
            risk_text="Backend local authorization fix for IDOR tenant leak and object-level permission.",
            skills=["backend-change-builder", "security-privacy-gate"],
            capabilities=["permission-boundary-modeling", "authentication-authorization"],
            risk_triggers=["object-level permission", "tenant leak"],
        )

        self.assertEqual(
            module._risk_match_strength("tenant data leak from identifier-only query", case),
            "strong",
        )

    def test_weak_match_does_not_satisfy_release_coverage(self) -> None:
        module = _load_module()
        case = module.RoutingCase(
            case_id="generic-auth-test",
            path="evals/routing/generic-auth-test.yaml",
            text="Auth test evidence risk change with backend-change-builder and regression-testing.",
            risk_text="Auth test evidence.",
            skills=["backend-change-builder"],
            capabilities=["regression-testing"],
            risk_triggers=["auth", "test"],
        )

        self.assertNotEqual(
            module._risk_match_strength("IDOR from missing object ownership check", case),
            "strong",
        )


if __name__ == "__main__":
    unittest.main()
