"""Shared fixture-owner access for mechanically split affected tests."""

from __future__ import annotations


def impact_fixture_owner():
    from tests.scripts.test_impact_graph import ImpactGraphResolutionTests

    return ImpactGraphResolutionTests


def core_fixture_owner():
    from tests.scripts.test_eval_core_principles import CorePrinciplesOutcomeTests

    return CorePrinciplesOutcomeTests


def core_fixture_symbols():
    from tests.scripts.test_eval_core_principles import (
        CorePrinciplesOutcomeTests,
        PROCESS_PASS,
    )

    return CorePrinciplesOutcomeTests, PROCESS_PASS
