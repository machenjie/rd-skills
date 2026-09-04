#!/usr/bin/env python3
"""Pure, versioned semantic contracts for Expert Panel currentness.

The projections in this module contain only behavior-affecting closed rules.
They deliberately exclude repository paths and bytes, runtime review identity,
dates, source selection, report presentation, and implementation helpers.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import re
import unicodedata
from typing import Any, Mapping


READABILITY_CURRENTNESS_CONTRACT_VERSION = (
    "readability-normalized-evidence-currentness-v4"
)
READABILITY_SOURCE_FINGERPRINT_KEYS = frozenset(
    {
        "readability_target_manifest",
        "readability_detector_contract",
        "actionability_detector_contract",
    }
)
READABILITY_LEGACY_SOURCE_FINGERPRINT_KEYS = frozenset(
    {
        "reference_content",
        "root_content",
        "ai_readability",
        "skill_detector",
    }
)
READABILITY_TARGET_BINDING_CONTRACT_ID = (
    "readability-normalized-target-review-binding-v4"
)
READABILITY_FINDING_BINDING_CONTRACT_ID = (
    "readability-normalized-finding-review-binding-v4"
)
READABILITY_TARGET_MANIFEST_CONTRACT_ID = (
    "readability-complete-normalized-binding-manifest-v4"
)
READABILITY_REVIEW_UNIT_BINDING_CONTRACT_ID = (
    "readability-normalized-review-unit-binding-v5"
)
READABILITY_VISIBLE_TEXT_CONTRACT_ID = (
    "readability-visible-text-and-sentence-boundaries-v2"
)
READABILITY_LOGICAL_UNIT_CONTRACT_ID = (
    "readability-normalized-logical-unit-v1"
)
READABILITY_FINDING_IDENTITY_CONTRACT_ID = (
    "readability-stable-finding-identity-v4"
)
READABILITY_DETECTOR_CONTRACT_ID = "ai-readability-detector-contract-v1"
ACTIONABILITY_DETECTOR_CONTRACT_ID = (
    "weak-front-loaded-action-detector-contract-v2"
)
READABILITY_ACTIONABILITY_FRONT_WINDOW_UNIT_LIMIT = 60
READABILITY_TARGET_REVIEW_FIELDS = {
    "content": (
        "path",
        "classification",
        "document_id",
        "owner",
        "document_part",
        "source_selector",
        "normalized_visible_text",
        "sentence_boundaries",
    ),
    "readability": (
        "document_id",
        "path",
        "surface",
        "document_part",
        "owner",
        "source_selector",
        "highest_band",
        "normalized_visible_text",
        "sentence_boundaries",
    ),
    "actionability": (
        "target_id",
        "skill_id",
        "path",
        "kind",
        "actionability_model",
        "front_loaded_action_score",
        "normalized_front_window",
    ),
}
READABILITY_FINDING_REVIEW_FIELDS = (
    "finding_id",
    "band",
    "words",
    "kind",
    "normalized_sentence",
)
READABILITY_CURRENTNESS_CONTRACT_PROJECTION = {
    "contract_version": READABILITY_CURRENTNESS_CONTRACT_VERSION,
    "source_currentness": {
        "current_keys": sorted(READABILITY_SOURCE_FINGERPRINT_KEYS),
        "legacy_keys": sorted(READABILITY_LEGACY_SOURCE_FINGERPRINT_KEYS),
        "legacy_policy": "structurally-valid-migration-required-not-current",
        "formal_policy": "current-three-key-shape-only",
    },
    "target_authority": {
        "manifest_contract_id": READABILITY_TARGET_MANIFEST_CONTRACT_ID,
        "categories": ["content", "readability", "actionability"],
        "target_binding_contract_id": READABILITY_TARGET_BINDING_CONTRACT_ID,
        "finding_binding_contract_id": READABILITY_FINDING_BINDING_CONTRACT_ID,
        "visible_text_contract_id": READABILITY_VISIBLE_TEXT_CONTRACT_ID,
        "logical_unit_contract_id": READABILITY_LOGICAL_UNIT_CONTRACT_ID,
        "finding_identity_contract_id": (
            READABILITY_FINDING_IDENTITY_CONTRACT_ID
        ),
        "review_unit_binding_contract": {
            "contract_id": READABILITY_REVIEW_UNIT_BINDING_CONTRACT_ID,
            "minimum_units": {
                "content": "target",
                "readability": "finding",
                "actionability": "target",
            },
            "inputs": [
                "binding_contract_id",
                "category",
                "target_id",
                "optional-finding-id",
                "local-authority-from-target-manifest",
            ],
            "document_outcome": "derived-from-finding-votes-not-stored",
        },
        "target_review_fields": {
            category: list(fields)
            for category, fields in sorted(
                READABILITY_TARGET_REVIEW_FIELDS.items()
            )
        },
        "finding_review_fields": list(READABILITY_FINDING_REVIEW_FIELDS),
        "ordering": "category-then-target-id-ascending",
        "nested_finding_ordering": "finding-id-ascending",
        "excludes": [
            "raw-content-fingerprint",
            "raw-context-span-and-window-sha256",
            "raw-line-offsets-and-columns",
            "markdown-presentation",
            "comments-and-frontmatter-metadata",
            "redundant-whitespace",
            "audit-report-metadata",
            "configured-selector-metadata",
            "review-state-and-review-reasons",
            "generated-output-metadata",
        ],
    },
    "storage_provenance": {
        "field": "review_artifacts",
        "decision": {"sha256": "required-lowercase-sha256"},
        "packet": {"sha256": "required-lowercase-sha256"},
        "ballots": {
            "count": 3,
            "fields": ["voter_id", "sha256"],
            "ordering": "voter-id-ascending",
        },
        "promotion": "exact-reprojection-from-validated-runtime-artifacts",
        "fixed_trust": "tracked-head-bytes-and-release-manifest-content-sha256",
        "raw_source_purpose": [
            "provenance",
            "artifact-integrity",
            "tamper-detection",
            "debug-audit",
        ],
        "raw_source_is_currentness_authority": False,
    },
    "detector_contracts": {
        "readability": READABILITY_DETECTOR_CONTRACT_ID,
        "actionability": ACTIONABILITY_DETECTOR_CONTRACT_ID,
        "actionability_selection": (
            "actionability-applicable-iff-weak-front-loaded-action-reason"
        ),
        "actionability_identity": "sha256-actionability-target-v1-path",
        "actionability_source": (
            "first-n-normalized-root-body-logical-units-with-raw-provenance"
        ),
        "actionability_front_window_unit_limit": (
            READABILITY_ACTIONABILITY_FRONT_WINDOW_UNIT_LIMIT
        ),
    },
    "authority_selection": {
        "fixed_path": "evals/expert-panel/readability.json",
        "config_selector_allowed": False,
        "match": [
            "current-target-authority-manifest",
            "current-detector-contracts",
            "review-contract-fingerprint",
            "exact-target-and-finding-coverage",
        ],
    },
}


SEMANTIC_DISPOSITION_CONTRACT_VERSION = (
    "semantic-disposition-stable-identity-evidence-currentness-v2"
)
SEMANTIC_DISPOSITION_RECORD_VERSION = "semantic-disposition-record-integrity-v1"
SEMANTIC_DISPOSITION_SOURCE_FINGERPRINT_KEYS = frozenset(
    {
        "root_candidate_manifest",
        "root_detector_contract",
        "reference_candidate_manifest",
        "reference_detector_contract",
    }
)
SEMANTIC_DISPOSITION_LEGACY_SOURCE_FINGERPRINT_KEYS = frozenset(
    {
        "audit",
        "root_source",
        "root_detector",
        "root_candidates",
        "root_context",
        "reference_source",
        "reference_detector",
        "reference_candidates",
        "reference_groups",
    }
)
_SEMANTIC_DETECTOR_COMPATIBILITY_ROWS = (
    {
        "compatibility_id": "semantic-015be10a-detector-contract-v1",
        "review_id": "semantic-015be10a-final-prep",
        "legacy_source_fingerprints": {
            "reference_candidate_manifest": (
                "dd03e7b80fe661d9db293db3d725706cd44a43ef7820de90452e22120e67638b"
            ),
            "reference_detector_contract": (
                "bb6182108495b202f41d3ca0d73cabe8e62f7433b54fe233d61fc4dcb7d4c06e"
            ),
            "root_candidate_manifest": (
                "8af1bbe28abcec952f7e52704f377324778002e2343a108fa3e2d0533ec7c919"
            ),
            "root_detector_contract": (
                "1ed220a953b74fd6d4e4594660999b53064177c885841ca744ca1dd06caf146d"
            ),
        },
        "current_source_fingerprints": {
            "reference_candidate_manifest": (
                "dd03e7b80fe661d9db293db3d725706cd44a43ef7820de90452e22120e67638b"
            ),
            "reference_detector_contract": (
                "b30afbeafb68bb21ade261d0ada1698865ccef20327dac0fe8edca4138ed1fcb"
            ),
            "root_candidate_manifest": (
                "8af1bbe28abcec952f7e52704f377324778002e2343a108fa3e2d0533ec7c919"
            ),
            "root_detector_contract": (
                "1553aac6b6640674967a676ff192ea933bd788a27b197dd8d8f0619f895564f0"
            ),
        },
        "legacy_detector_contracts": {
            "root_detector_contract": (
                "1ed220a953b74fd6d4e4594660999b53064177c885841ca744ca1dd06caf146d"
            ),
            "reference_detector_contract": (
                "bb6182108495b202f41d3ca0d73cabe8e62f7433b54fe233d61fc4dcb7d4c06e"
            ),
        },
        "current_detector_contracts": {
            "root_detector_contract": (
                "1553aac6b6640674967a676ff192ea933bd788a27b197dd8d8f0619f895564f0"
            ),
            "reference_detector_contract": (
                "b30afbeafb68bb21ade261d0ada1698865ccef20327dac0fe8edca4138ed1fcb"
            ),
        },
        "review_contract_fingerprint": (
            "6f9618afabdc84a4e39a6cfe30b24b4b7b22f431f4d77a6337923af82f43069e"
        ),
        "target_count": 197,
        "axis_counts": {"reference": 121, "root": 76},
    },
)
SEMANTIC_DISPOSITION_CONTRACT_PROJECTION = {
    "contract_version": SEMANTIC_DISPOSITION_CONTRACT_VERSION,
    "source_currentness": {
        "current_keys": sorted(SEMANTIC_DISPOSITION_SOURCE_FINGERPRINT_KEYS),
        "legacy_keys": sorted(
            SEMANTIC_DISPOSITION_LEGACY_SOURCE_FINGERPRINT_KEYS
        ),
        "legacy_policy": "structurally-valid-migration-required-not-current",
        "formal_policy": "current-four-key-shape-only",
    },
    "candidate_manifests": {
        "axes": ["reference", "root"],
        "identity": "axis-colon-candidate-id",
        "root_eligibility": "all-canonical-root-candidates",
        "reference_eligibility": "detector-status-candidate-only",
        "ordering": "target-id-ascending",
        "binding": "stable-identity-plus-current-evidence-v2",
        "stable_identity": [
            "owner",
            "finding-type",
            "stable-source-selector",
            "semantic-section-or-shape-identity",
        ],
        "evidence": [
            "candidate-text",
            "occurrences",
            "membership",
            "normalized-content",
        ],
        "evidence_change": "same-target-id-needs-confirmation",
        "selector_change": "new-target-id",
        "collision_policy": "deterministic-fail-closed-no-content-line-ordinal-member-fallback",
        "excludes": [
            "configured-dispositions",
            "audit-report-metadata",
            "application-status",
            "fixed-attestation-selector-metadata",
            "physical-line-coordinates",
        ],
    },
    "detector_contracts": {
        "root": "collector-owned-root-detector-fingerprint",
        "reference": "closed-audit-schema-families-thresholds-limitations",
    },
    "authority_selection": {
        "fixed_path": "evals/expert-panel/semantic-disposition.json",
        "candidate_modes": ["ordinary", "root", "reference", "both"],
        "match": [
            "current-candidate-manifests",
            "current-detector-contracts",
            "review-contract-fingerprint",
            "exact-target-id-coverage",
        ],
        "required_match_count": 1,
        "config_selector_allowed": False,
    },
    "configuration": {
        "migration": "all-or-nothing-current-schema",
        "record_integrity": SEMANTIC_DISPOSITION_RECORD_VERSION,
        "legacy_or_partial": "reject",
    },
}


PROFESSIONAL_SCHEMA3_CONTRACT_VERSION = (
    "professional-completeness-schema3-review-carry-v3"
)
PROFESSIONAL_SCHEMA3_SCHEMA_VERSION = 3
PROFESSIONAL_PANEL_SIZE = 3
PROFESSIONAL_MINIMUM_WINNING_VOTES = 2
PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS = 2
PROFESSIONAL_REQUIRED_ARCHITECTURE_EXPERTS = 1
PROFESSIONAL_MAXIMUM_PLAN_LINEAGE_DEPTH = 8
PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG = "skill-reference-architecture"

PROFESSIONAL_PACKET_KIND = (
    "changeforge.professional-completeness-panel-packet"
)
PROFESSIONAL_BALLOT_KIND = (
    "changeforge.professional-completeness-panel-ballot"
)
PROFESSIONAL_DECISION_KIND = (
    "changeforge.professional-completeness-panel-decision"
)
PROFESSIONAL_REVIEW_CAPSULE_KIND = (
    "changeforge.professional-completeness-review-capsule"
)
PROFESSIONAL_DISCOVERY_CAPSULE_KIND = (
    "changeforge.professional-completeness-discovery-capsule"
)
PROFESSIONAL_CANDIDATE_REQUEST_KIND = (
    "changeforge.professional-completeness-candidate-request"
)

PROFESSIONAL_DECISION_METHOD = (
    "per-skill-qualified-reviewer-pool-domain-critical-fail-closed"
)
PROFESSIONAL_INCREMENTAL_DECISION_METHOD = (
    "exact-package-carry-forward-qualified-reviewer-pool-domain-critical-fail-closed"
)
PROFESSIONAL_CRITERIA = {
    "professional-correctness": (
        "Rules and decisions are professionally correct for the named capability."
    ),
    "material-omissions": (
        "No material expert decision, failure mechanism, or operational obligation is missing."
    ),
    "failure-modes": "Triggered failure modes and recovery limits are covered.",
    "boundary-conditions": "Material edge cases and authority boundaries are explicit.",
    "verification-methods": (
        "Claims and outputs have proportionate verification methods."
    ),
    "erroneous-rules": (
        "No misleading, unsafe, obsolete, or internally conflicting rule remains."
    ),
    "adjacent-overlap-or-gap": (
        "Adjacent Skills have neither material responsibility overlap nor an uncovered gap."
    ),
    "generic-knowledge-pollution": (
        "The package excludes generic knowledge that does not justify context cost."
    ),
    "reference-high-risk-coverage": (
        "Indexed References cover the high-risk decisions delegated by the root Skill."
    ),
    "output-verifiability": (
        "The output contract produces reviewable, verifiable evidence."
    ),
}
PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA = {
    "professional-correctness",
    "erroneous-rules",
    "material-omissions",
    "failure-modes",
    "boundary-conditions",
    "verification-methods",
}
PROFESSIONAL_ORDINARY_CRITERIA = (
    set(PROFESSIONAL_CRITERIA) - PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
)
PROFESSIONAL_CRITERION_VALUES = {"satisfied", "defect-found"}
PROFESSIONAL_ACCEPTED_DISPOSITION = (
    "accepted-current-professional-completeness"
)
PROFESSIONAL_CORRECTION_DISPOSITION = "requires-professional-correction"
PROFESSIONAL_UNRESOLVED_DISPOSITION = (
    "unresolved-professional-disagreement"
)
PROFESSIONAL_DECISIONS = {
    PROFESSIONAL_ACCEPTED_DISPOSITION,
    PROFESSIONAL_CORRECTION_DISPOSITION,
}
PROFESSIONAL_FINAL_DISPOSITIONS = {
    *PROFESSIONAL_DECISIONS,
    PROFESSIONAL_UNRESOLVED_DISPOSITION,
}
PROFESSIONAL_REASON_CODES = {
    PROFESSIONAL_ACCEPTED_DISPOSITION: {
        "all-professional-criteria-satisfied",
    },
    PROFESSIONAL_CORRECTION_DISPOSITION: {
        "adjacent-responsibility-gap",
        "boundary-condition-gap",
        "erroneous-professional-rule",
        "failure-mode-gap",
        "generic-knowledge-pollution",
        "material-professional-omission",
        "output-verification-gap",
        "professional-correctness-defect",
        "reference-high-risk-coverage-gap",
        "verification-method-gap",
    },
}
PROFESSIONAL_REVIEW_OUTCOMES = {"covered", "not-applicable", "defect-found"}
PROFESSIONAL_ADJACENCY_DISPOSITIONS = {
    "adjacent-no-gap",
    "not-adjacent",
    "gap-or-overlap-defect",
}

PROFESSIONAL_ADJACENCY_ALGORITHM = "catalog-semantic-overlap-v3"
PROFESSIONAL_ADJACENCY_SELECTION_VERSION = "layered-required-candidates-v2"
PROFESSIONAL_SOURCE_DECLARED_SELECTION_VERSION = (
    "directional-decision-bearing-code-span-v1"
)
PROFESSIONAL_SOURCE_DECLARED_CONTEXTS = (
    "imperative-route-or-handoff-sentence",
    "routing-owner-risk-gate-verification-handoff-table-cell",
)
PROFESSIONAL_SOURCE_DECLARED_EXCLUDED_SURFACES = (
    "frontmatter",
    "fenced-code",
    "example-history-background-sections",
    "generated-layer3-delivery",
)
PROFESSIONAL_NEGATIVE_ROUTE_MATCH_VERSION = "phrase-aware-v1"
PROFESSIONAL_ADJACENCY_TOP_K = 5
PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K = 2
PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET = 57
PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT = 162
PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL = 3500
PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT = 30
PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS = 2
PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS = {
    "trigger-overlap": 5,
    "output-overlap": 4,
    "responsibility-overlap": 2,
    "reference-topic-overlap": 3,
    "negative-route-conflict": 4,
}
PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS = tuple(
    sorted(set(PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS) - {"negative-route-conflict"})
)
PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS = frozenset(
    {
        "actual",
        "already",
        "behavior",
        "change",
        "changes",
        "decision",
        "define",
        "design",
        "implementation",
        "local",
        "ordinary",
        "ready",
        "required",
        "scope",
        "select",
        "specific",
        "work",
    }
)
PROFESSIONAL_ADJACENCY_STOP_WORDS = frozenset(
    {
        "and",
        "are",
        "for",
        "from",
        "into",
        "not",
        "only",
        "output",
        "skill",
        "task",
        "that",
        "the",
        "this",
        "when",
        "with",
    }
)
PROFESSIONAL_EVIDENCE_STOP_WORDS = PROFESSIONAL_ADJACENCY_STOP_WORDS | frozenset(
    {
        "anchor",
        "bound",
        "candidate",
        "claim",
        "complete",
        "criterion",
        "current",
        "evidence",
        "examined",
        "explicit",
        "explicitly",
        "failure",
        "lines",
        "material",
        "omission",
        "package",
        "professional",
        "provides",
        "review",
        "reviewed",
        "source",
        "supports",
    }
)
PROFESSIONAL_GROUNDING_STOP_WORDS = PROFESSIONAL_EVIDENCE_STOP_WORDS | frozenset(
    {"cited", "documented", "reviewer", "satisfied"}
)
PROFESSIONAL_MINIMUM_EXAMINED_ITEMS = 2
PROFESSIONAL_MINIMUM_ASSERTION_OVERLAP_TOKENS = 2
PROFESSIONAL_MINIMUM_EXAMINED_ITEM_OVERLAP_TOKENS = 2
PROFESSIONAL_MINIMUM_ADJACENCY_SIDE_OVERLAP_TOKENS = 1

PROFESSIONAL_SEMANTIC_GROUNDING_CONTRACT = {
    "algorithm": "schema3-contiguous-source-grounding-v1",
    "coordinates": "anchor-local-lines-no-cross-line-or-anchor-phrases",
    "lexical_adjacency": "raw-stream-no-generic-token-gap-bridging",
    "nondefect_anchor_requirement": "one-exact-nongeneric-bigram",
    "defect_anchor_requirement": (
        "one-exact-nongeneric-bigram-or-three-distinct-grounded-unigrams"
    ),
    "adjacency_nondefect_requirement": (
        "one-exact-nongeneric-bigram-from-each-side"
    ),
    "adjacency_defect_requirement": (
        "nondefect-requirement-or-one-unigram-each-side-and-six-total"
    ),
    "uniform_template_guard": {
        "ordinary_ngram_size": 5,
        "short_claim_max_tokens": 10,
        "short_claim_ngram_size": 4,
        "minimum_uniform_claims": 4,
        "minimum_uniform_share_percent": 80,
        "maximum_grounded_bigrams_for_low_grounding": 1,
        "shared_template_must_have_source_bigram": True,
    },
}

PROFESSIONAL_CURRENTNESS_PROJECTION_VERSION = (
    "professional-commonmark-material-projection-v4"
)
PROFESSIONAL_CURRENTNESS_PROJECTION_CONTRACT = {
    "version": PROFESSIONAL_CURRENTNESS_PROJECTION_VERSION,
    "purpose": "deterministic-professional-currentness-only",
    "content_fingerprint_role": "raw-provenance-integrity-tamper-debug-only",
    "normalization": [
        "unicode-nfc",
        "line-endings-to-lf",
        "parser-authenticated-horizontal-whitespace-and-softbreak",
        "parser-authenticated-emphasis-and-strong-decoration",
        "parser-authenticated-unordered-list-marker",
        "parser-authenticated-root-level-source-marker-comments",
        "exact-column-zero-closed-simple-frontmatter",
    ],
    "parser": {
        "distributions": {
            "markdown-it-py": "4.2.0",
            "mdurl": "0.1.2",
        },
        "preset": "commonmark",
        "options": {
            "html": True,
            "linkify": False,
            "typographer": False,
            "breaks": False,
        },
        "enabled_rules": ["table-recognition-only"],
        "active_rules": {
            "core": ["normalize", "block", "inline", "text_join"],
            "block": [
                "table",
                "code",
                "fence",
                "blockquote",
                "hr",
                "list",
                "reference",
                "html_block",
                "heading",
                "lheading",
                "paragraph",
            ],
            "inline": [
                "text",
                "newline",
                "escape",
                "backticks",
                "emphasis",
                "link",
                "image",
                "autolink",
                "html_inline",
                "entity",
            ],
            "inline2": ["balance_pairs", "emphasis", "fragments_join"],
        },
        "version_mismatch": "fail-closed",
    },
    "preserved_material": [
        "exact-lexical-text-case-punctuation-and-word-order",
        "heading-text-and-level",
        "paragraph-heading-blockquote-list-code-link-image-type-and-order",
        "list-nesting",
        "fenced-and-inline-code-content",
        "direct-link-image-and-commonmark-autolink-attributes",
        "inline-boundary-whitespace",
        "hardbreak",
        "complete-registry-authority",
        "ordered-reference-contract-v2-authority",
        "required-expertise",
        "package-identity-layer-and-owned-source-paths",
    ],
    "ignored_comment_classes": [
        "rd-semantic-id-v2-source-marker",
        "changeforge-generated-boundary-marker",
        "changeforge-contract-boundary-marker",
    ],
    "structured_authority": {
        "registry": "complete-canonical-validated-row",
        "reference": "ordered-exact-reference-contract-v2-records",
        "compatibility-responsibility": (
            "derived-from-registry-authority-and-must-not-drift"
        ),
        "list_order": "preserved-unless-upstream-contract-canonicalizes-it",
    },
    "natural_language_equivalence_inference": "forbidden",
    "closed_block_token_subset": [
        "document",
        "plain-paragraph",
        "heading-with-level",
        "blockquote",
        "bullet-list-and-list-item",
        "fenced-code-with-info-and-content",
        "indented-code",
        "thematic-break",
    ],
    "closed_inline_token_subset": [
        "text-and-softbreak-as-whitespace-aware-fragments",
        "hardbreak",
        "emphasis-and-strong-children",
        "inline-code",
        "direct-link",
        "image",
        "commonmark-autolink",
    ],
    "preserved_token_authority": [
        "heading-level",
        "block-and-inline-type-order-and-nesting",
        "fence-info-and-content",
        "indented-code-content",
        "link-and-image-exact-parser-attributes",
        "inline-code-content",
    ],
    "opaque_document": {
        "normalization": [
            "line-endings-to-lf",
            "unicode-nfc",
            "remove-exact-authenticated-full-line-source-markers",
        ],
        "preserved_exactly": [
            "all-other-characters",
            "horizontal-whitespace",
            "blank-line-whitespace",
            "final-newline",
        ],
        "whole_body_triggers": [
            "ordered-list",
            "gfm-table",
            "raw-html",
            "reference-definition-or-reference-style-link",
            "unknown-or-plugin-token",
            "unexpected-token-attributes-metadata-or-nesting",
        ],
        "authenticated_marker_removal_scope": (
            "parser-confirmed-root-level-single-line-exact-comments-only"
        ),
        "marker_reparse_required": True,
    },
    "unsupported_markdown": (
        "unsupported-or-ambiguous-markdown-is-opaque-and-change-is-fresh"
    ),
}

PROFESSIONAL_CARRY_CONTRACT = {
    "carry_unit": "whole-professional-package",
    "baseline_requirement": "canonical-prior-material-review-snapshot",
    "review_contract_requirement": "exact-fingerprint-match",
    "dependency_depth": "one-hop-material-review-authority",
    "required_dependency_sources": [
        "packet-required-candidate",
        "reviewer-added-candidate-union-from-all-prior-target-ballots",
    ],
    "content_fingerprint_purpose": [
        "provenance",
        "artifact-integrity",
        "tamper-detection",
        "debug-audit",
    ],
    "content_fingerprint_is_review_routing_authority": False,
    "currentness_authority": [
        PROFESSIONAL_CURRENTNESS_PROJECTION_VERSION,
        "complete-registry-authority",
        "ordered-reference-contract-v2-authority",
        "conservative-professional-source-material",
        "required-expertise",
        "required-adjacency-relationships",
    ],
    "target_selection_authority": [
        "selection-contract-version",
        "required-candidate-ids",
        "required-candidate-material-bindings",
    ],
    "diagnostic_only_target_context": [
        "full-catalog-ranking",
        "non-selected-ranking-metadata",
    ],
    "fresh_state_is_not_a_dependency": True,
    "accepted_prior_disposition": PROFESSIONAL_ACCEPTED_DISPOSITION,
}
PROFESSIONAL_REVIEW_CAPSULE_CONTRACT = {
    "projection": "final-assigned-fresh-target-review-capsule",
    "target_material": (
        "complete-own-material-registry-reference-authority-expertise"
    ),
    "adjacency_metadata": "complete-full-ranking-and-required-selection",
    "candidate_material": "complete-raw-material-without-candidate-ranking",
    "candidate_origins": ["packet-required", "reviewer-added"],
    "reviewer_added_source": "validated-immutable-candidate-request",
    "predecessor": "immutable-discovery-capsule",
    "material_storage": "top-level-skill-deduplicated-catalog",
    "closed_projection": True,
}
PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT = {
    "projection": "assigned-fresh-target-discovery-capsule",
    "target_material": (
        "complete-own-material-registry-reference-authority-expertise"
    ),
    "required_candidate_material": "complete-raw-material-without-candidate-ranking",
    "adjacency_metadata": "complete-full-ranking-and-required-selection",
    "candidate_boundary_catalog": (
        "complete-lightweight-responsibility-reference-authority-catalog"
    ),
    "candidate_request": "separate-immutable-artifact-required",
    "material_storage": "top-level-skill-deduplicated-catalog",
    "closed_projection": True,
}

PROFESSIONAL_TARGET_BINDING_CONTRACT_VERSION = (
    "professional-target-conservative-currentness-binding-v6"
)
PROFESSIONAL_DEPENDENCY_BINDING_CONTRACT_VERSION = (
    "professional-one-hop-material-dependency-binding-v4"
)
PROFESSIONAL_MATERIAL_RECORD_FIELDS = {
    "path",
    "sha256",
    "line_count",
    "content",
}
PROFESSIONAL_ADJACENCY_REVIEW_BINDING_FIELDS = {
    "required_candidate_ids",
    "selection_contract_version",
}
PROFESSIONAL_SEMANTIC_RESPONSIBILITY_FIELDS = {
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "layer3_candidates",
    "used_by",
    "boundary_signals",
    "group",
    "content_class",
    "delivery_scope",
    "task_routable",
}
PROFESSIONAL_SEMANTIC_RESPONSIBILITY_REQUIRED_LIST_FIELDS = {
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
}
PROFESSIONAL_SEMANTIC_RESPONSIBILITY_OPTIONAL_LIST_FIELDS = {
    "layer3_candidates",
    "used_by",
    "boundary_signals",
}
PROFESSIONAL_REGISTRY_AUTHORITY_REQUIRED_FIELDS = {
    "name",
    "path",
    "required_expertise_tags",
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "reference_index",
}
PROFESSIONAL_REFERENCE_AUTHORITY_FIELDS = {
    "path",
    "type",
    "load_when",
    "do_not_load_when",
    "required_by",
    "required_output",
}
PROFESSIONAL_REQUIRED_CANDIDATE_MATERIAL_BINDING_FIELDS = {
    "skill_id",
    "material_fingerprint",
}
PROFESSIONAL_TARGET_BINDING_FIELDS = {
    "skill_id",
    "layer",
    "own_material",
    "registry",
    "registry_authority",
    "reference_authority",
    "required_expertise_tags",
    "adjacency",
    "content_fingerprint",
    "package_material_binding",
    "dependency_material_bindings",
    "review_unit_binding",
}
PROFESSIONAL_SNAPSHOT_TARGET_FIELDS = {
    "skill_id",
    "layer",
    "package_material_binding",
    "dependency_material_bindings",
    "review_unit_binding",
}
PROFESSIONAL_DECISION_DEPENDENCY_FIELDS = {
    "skill_id",
    "final_disposition",
    "evidence_complete",
    "prior_target_vote_count",
    "required_candidate_ids",
    "reviewer_added_candidate_ids_union",
    "dependency_candidate_ids",
}

PROFESSIONAL_COMPACT_AUTHORITY_CONTRACT_VERSION = (
    "professional-target-current-material-authority-v6"
)
PROFESSIONAL_COMPACT_AUTHORITY_FIELDS = {
    "package_material_binding",
    "review_unit_binding",
    "required_expertise_tags",
    "selection_contract_version",
    "required_candidate_ids",
    "required_candidate_material_bindings",
    "reviewer_added_candidate_ids_union",
    "reviewer_added_candidate_material_bindings",
    "vote_authorities",
    "reviewer_partition",
    "evidence_metrics",
    "origin",
}

PROFESSIONAL_COMPACT_VOTE_CONTRACT_VERSION = (
    "professional-compact-vote-projection-v1"
)
PROFESSIONAL_COMPACT_VOTE_FIELDS = {
    "reviewer",
    "decision",
    "reason_code",
    "review_evidence_fingerprint",
    "criteria",
    "examined_failure_modes",
    "examined_omission_candidates",
    "examined_adjacent_candidates",
    "proof_limits",
    "rationale",
}
PROFESSIONAL_COMPACT_CRITERIA_FIELDS = {
    "ordinary",
    "domain_critical_defects",
}
PROFESSIONAL_COMPACT_COLLECTION_FIELDS = {"count", "defect_count", "digest"}
PROFESSIONAL_COMPACT_ADJACENCY_FIELDS = {
    "count",
    "required_count",
    "reviewer_added_candidate_ids",
    "defect_count",
    "digest",
}
PROFESSIONAL_COMPACT_PROOF_LIMIT_FIELDS = {"count", "digest", "bounded"}
PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_MAXIMUM = 256
PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_COUNT = 2
PROFESSIONAL_COMPACT_RATIONALE_MAXIMUM = 512


def professional_semantic_grounding_contract() -> dict[str, Any]:
    """Return a detached copy of the closed schema-3 grounding rules."""

    return copy.deepcopy(PROFESSIONAL_SEMANTIC_GROUNDING_CONTRACT)


def readability_currentness_contract_projection() -> dict[str, Any]:
    """Return the closed Readability currentness and binding rules."""

    return copy.deepcopy(READABILITY_CURRENTNESS_CONTRACT_PROJECTION)


_READABILITY_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_READABILITY_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
_READABILITY_ATX_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_READABILITY_LIST_MARKER_RE = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"
)
_READABILITY_LIST_ITEM_RE = re.compile(
    r"^(?P<indent>\s*)(?:[-*+]|\d+[.)])\s+(?P<text>.*)$"
)
_READABILITY_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_READABILITY_REFERENCE_LINK_RE = re.compile(r"!?\[([^\]]*)\]\[[^\]]*\]")
_READABILITY_REFERENCE_DEFINITION_RE = re.compile(
    r"^\s{0,3}\[[^\]]+\]:\s+\S+.*$"
)
_READABILITY_INLINE_CODE_RE = re.compile(r"`([^`\n]*)`")
_READABILITY_AUTOLINK_RE = re.compile(r"<((?:https?://|mailto:)[^ >]+)>")
_READABILITY_HTML_TAG_RE = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^>]*)?/?>"
)
_READABILITY_SETEXT_OR_THEMATIC_RE = re.compile(
    r"^\s{0,3}(?:=+|(?:-\s*){3,}|(?:\*\s*){3,}|(?:_\s*){3,})\s*$"
)
_READABILITY_EMPHASIS_RE = re.compile(
    r"(?<!\w)(\*\*|__|~~|\*|_)(?=\S)(.+?)(?<=\S)\1(?!\w)"
)
_READABILITY_SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Za-z0-9])"
)
_READABILITY_SENTENCE_ABBREVIATIONS = frozenset(
    {
        "e.g.",
        "i.e.",
        "etc.",
        "vs.",
        "mr.",
        "mrs.",
        "ms.",
        "dr.",
        "prof.",
        "sr.",
        "jr.",
        "no.",
    }
)
_LOWERCASE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _readability_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-blank text")
    return value


def _readability_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _LOWERCASE_SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase sha256")
    return value


def _readability_preserve_newlines(match: re.Match[str], *, space: bool) -> str:
    return (" " if space else "") + ("\n" * match.group(0).count("\n"))


def _readability_source_lines(
    value: object, *, strip_frontmatter: bool
) -> list[tuple[int, str]]:
    """Remove hidden raw HTML before decoding visible escaped syntax."""

    text = _readability_text(value, label="readability visible source")
    text = _READABILITY_AUTOLINK_RE.sub(lambda match: match.group(1), text)
    text = _READABILITY_COMMENT_RE.sub(
        lambda match: _readability_preserve_newlines(match, space=False),
        text,
    )
    text = _READABILITY_HTML_TAG_RE.sub(
        lambda match: _readability_preserve_newlines(match, space=True),
        text,
    )
    text = unicodedata.normalize("NFKC", html.unescape(text))
    lines = text.splitlines()
    start = 0
    if strip_frontmatter and lines and lines[0].strip() == "---":
        end = next(
            (
                index
                for index, line in enumerate(lines[1:], start=1)
                if line.strip() == "---"
            ),
            None,
        )
        if end is not None:
            start = end + 1
    return [
        (line_number, line)
        for line_number, line in enumerate(lines[start:], start=start + 1)
    ]


def _readability_normalize_fragment(value: str, *, literal: bool = False) -> str:
    rendered = value.strip()
    if literal:
        return re.sub(r"\s+", " ", rendered).strip()
    if rendered.startswith("|") and rendered.count("|") >= 2:
        rendered = " ".join(
            cell.strip() for cell in rendered.strip("|").split("|")
        )
    rendered = _READABILITY_ATX_HEADING_RE.sub("", rendered)
    rendered = re.sub(r"\s+#+\s*$", "", rendered)
    rendered = re.sub(r"^\s*(?:>\s*)+", "", rendered)
    rendered = _READABILITY_LIST_MARKER_RE.sub("", rendered)
    rendered = re.sub(r"^\[[ xX]\]\s+", "", rendered)
    rendered = _READABILITY_LINK_RE.sub(lambda match: match.group(1), rendered)
    rendered = _READABILITY_REFERENCE_LINK_RE.sub(
        lambda match: match.group(1), rendered
    )
    rendered = _READABILITY_INLINE_CODE_RE.sub(
        lambda match: match.group(1), rendered
    )
    rendered = re.sub(r"\\([\\`*{}\[\]()#+.!_>~-])", r"\1", rendered)
    while True:
        unwrapped = _READABILITY_EMPHASIS_RE.sub(
            lambda match: match.group(2), rendered
        )
        if unwrapped == rendered:
            break
        rendered = unwrapped
    return re.sub(r"\s+", " ", rendered).strip()


def readability_normalized_logical_units(
    value: object,
    *,
    exclude_fenced: bool = False,
    strip_frontmatter: bool = True,
) -> list[dict[str, Any]]:
    """Project presentation-insensitive logical units with raw line provenance."""

    units: list[dict[str, Any]] = []
    current_kind: str | None = None
    current_parts: list[tuple[int, str]] = []
    current_indent = 0
    fence_marker: str | None = None

    def flush() -> None:
        nonlocal current_kind, current_parts, current_indent
        if current_parts:
            normalized = " ".join(
                part
                for part in (
                    _readability_normalize_fragment(
                        text,
                        literal=current_kind == "fenced",
                    )
                    for _line, text in current_parts
                )
                if part
            )
            normalized = re.sub(r"\s+", " ", normalized).strip()
            if normalized:
                units.append(
                    {
                        "ordinal": len(units) + 1,
                        "kind": current_kind,
                        "text": normalized,
                        "start_line": current_parts[0][0],
                        "end_line": current_parts[-1][0],
                        "source_lines": [line for line, _text in current_parts],
                    }
                )
        current_kind = None
        current_parts = []
        current_indent = 0

    for line_number, raw_line in _readability_source_lines(
        value,
        strip_frontmatter=strip_frontmatter,
    ):
        fence = _READABILITY_FENCE_RE.match(raw_line)
        if fence is not None:
            marker = fence.group(1)[0]
            if fence_marker is None:
                flush()
                fence_marker = marker
                if not exclude_fenced:
                    current_kind = "fenced"
            elif marker == fence_marker:
                flush()
                fence_marker = None
            continue
        if fence_marker is not None:
            if not exclude_fenced and raw_line.strip():
                current_parts.append((line_number, raw_line))
            continue

        structural = re.sub(r"^\s*(?:>\s*)+", "", raw_line)
        stripped = structural.strip()
        if not stripped:
            continue
        if _READABILITY_REFERENCE_DEFINITION_RE.fullmatch(structural) is not None:
            continue
        if _READABILITY_SETEXT_OR_THEMATIC_RE.fullmatch(structural) is not None:
            flush()
            continue
        if stripped.startswith("|") and stripped.count("|") >= 2:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and all(
                re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
            ):
                continue
            flush()
            current_kind = "table-row"
            current_parts = [(line_number, structural)]
            flush()
            continue

        list_item = _READABILITY_LIST_ITEM_RE.match(structural)
        if list_item is not None:
            flush()
            current_kind = "list-item"
            current_indent = len(
                structural[: list_item.start("text")].expandtabs(4)
            )
            current_parts = [(line_number, list_item.group("text"))]
            continue
        line_indent = len(structural) - len(structural.lstrip(" \t"))
        if current_kind == "list-item" and line_indent >= current_indent:
            current_parts.append((line_number, stripped))
            continue
        if current_kind == "list-item":
            flush()

        if _READABILITY_ATX_HEADING_RE.match(structural) is not None:
            flush()
            current_kind = "heading"
            current_parts = [(line_number, structural)]
            flush()
            continue
        if current_kind != "prose":
            flush()
            current_kind = "prose"
        current_parts.append((line_number, structural))
    flush()
    return units


def readability_normalized_visible_text(
    value: object, *, exclude_fenced: bool = False
) -> str:
    """Return presentation-insensitive text used only for Readability routing.

    Exact source bytes remain in the review packet and are validated separately.
    This projection removes only Markdown/YAML presentation that the closed
    Readability detectors do not judge.
    """

    return " ".join(
        unit["text"]
        for unit in readability_normalized_logical_units(
            value,
            exclude_fenced=exclude_fenced,
        )
    )


def readability_sentence_boundaries(visible_text: object) -> list[dict[str, Any]]:
    """Split normalized visible text into stable, explicit sentence units."""

    text = _readability_text(visible_text, label="normalized readability text")
    result: list[dict[str, Any]] = []
    start = 0
    for boundary in _READABILITY_SENTENCE_BOUNDARY_RE.finditer(text):
        prefix = text[: boundary.start()].casefold()
        abbreviation = re.search(
            r"(?:^|[^a-z0-9])([a-z]+(?:\.[a-z]+)*)\.$", prefix
        )
        if (
            abbreviation is not None
            and f"{abbreviation.group(1)}." in _READABILITY_SENTENCE_ABBREVIATIONS
        ) or re.search(r"(?:^|\s)[a-z]\.$", prefix):
            continue
        sentence = text[start : boundary.start()].strip()
        if sentence:
            sentence_start = text.find(sentence, start, boundary.start())
            result.append(
                {
                    "ordinal": len(result) + 1,
                    "start_offset": sentence_start,
                    "end_offset": sentence_start + len(sentence),
                    "text": sentence,
                }
            )
        start = boundary.end()
    sentence = text[start:].strip()
    if sentence:
        sentence_start = text.find(sentence, start)
        result.append(
            {
                "ordinal": len(result) + 1,
                "start_offset": sentence_start,
                "end_offset": sentence_start + len(sentence),
                "text": sentence,
            }
        )
    return result


def readability_visible_text_projection(
    value: object, *, exclude_fenced: bool = False
) -> dict[str, Any]:
    normalized = readability_normalized_visible_text(
        value, exclude_fenced=exclude_fenced
    )
    if not normalized:
        raise ValueError("readability visible source has no governed text")
    return {
        "contract_id": READABILITY_VISIBLE_TEXT_CONTRACT_ID,
        "normalized_visible_text": normalized,
        "sentence_boundaries": readability_sentence_boundaries(normalized),
    }


def readability_stable_finding_id(
    *, document_id: object, kind: object, sentence: object, occurrence: object
) -> str:
    """Identify one finding without raw lines, offsets, spans, or presentation."""

    identity = {
        "contract_id": READABILITY_FINDING_IDENTITY_CONTRACT_ID,
        "document_id": _readability_text(document_id, label="document_id"),
        "kind": _readability_text(kind, label="finding kind"),
        "normalized_sentence": readability_normalized_visible_text(sentence),
        "occurrence": occurrence,
    }
    if not identity["normalized_sentence"]:
        raise ValueError("finding normalized sentence must be non-blank")
    if type(occurrence) is not int or occurrence < 1:
        raise ValueError("finding occurrence must be a positive integer")
    return canonical_json_sha256(identity)


def readability_target_review_projection(
    *, category: str, target: Mapping[str, Any]
) -> dict[str, Any]:
    """Project only normalized evidence that can change Readability judgment."""

    if category not in READABILITY_TARGET_REVIEW_FIELDS or not isinstance(
        target, Mapping
    ):
        raise ValueError("readability target review projection input is invalid")
    identity_fields = {
        "content": (
            "path", "classification", "document_id", "owner",
            "document_part", "source_selector",
        ),
        "readability": (
            "document_id", "path", "surface", "document_part", "owner",
            "source_selector", "highest_band",
        ),
        "actionability": (
            "target_id", "skill_id", "path", "kind", "actionability_model",
            "front_loaded_action_score",
        ),
    }[category]
    missing = [field for field in identity_fields if field not in target]
    if missing:
        raise ValueError(
            "readability target review projection is missing "
            + ", ".join(missing)
        )
    projection = {
        field: copy.deepcopy(target[field]) for field in identity_fields
    }
    if category in {"content", "readability"}:
        context = target.get("document_context")
        if not isinstance(context, Mapping) or "text" not in context:
            raise ValueError("readability target document context is invalid")
        projection.update(readability_visible_text_projection(context["text"]))
    else:
        window = target.get("front_window")
        lines = window.get("lines") if isinstance(window, Mapping) else None
        if not isinstance(lines, list) or not lines or any(
            not isinstance(row, Mapping) or not isinstance(row.get("text"), str)
            for row in lines
        ):
            raise ValueError("actionability front window is invalid")
        logical_units = readability_normalized_logical_units(
            "\n".join(str(row["text"]) for row in lines),
            exclude_fenced=True,
            strip_frontmatter=False,
        )
        if not logical_units:
            raise ValueError("actionability front window has no governed units")
        if len(logical_units) > (
            READABILITY_ACTIONABILITY_FRONT_WINDOW_UNIT_LIMIT
        ):
            raise ValueError("actionability front window exceeds static unit limit")
        projection["normalized_front_window"] = {
            "contract_id": READABILITY_LOGICAL_UNIT_CONTRACT_ID,
            "units": [
                {"ordinal": index, "text": unit["text"]}
                for index, unit in enumerate(logical_units, start=1)
            ],
        }
    return projection


def readability_finding_review_projection(
    *, finding: Mapping[str, Any]
) -> dict[str, Any]:
    """Project normalized detector evidence while retaining raw data elsewhere."""

    if not isinstance(finding, Mapping):
        raise ValueError("readability finding review projection input is invalid")
    required = {"finding_id", "band", "words", "kind", "sentence", "sentence_fingerprint"}
    missing = sorted(required - set(finding))
    if missing:
        raise ValueError(
            "readability finding review projection is missing "
            + ", ".join(missing)
        )
    sentence = _readability_text(
        finding["sentence"], label="readability finding sentence"
    )
    raw_fingerprint = _readability_sha256(
        finding["sentence_fingerprint"],
        label="readability finding sentence fingerprint",
    )
    expected_raw = hashlib.sha256(
        ("ai-readability-sentence-v1\0" + sentence).encode("utf-8")
    ).hexdigest()
    if raw_fingerprint != expected_raw:
        raise ValueError("readability finding sentence fingerprint is stale")
    normalized = readability_normalized_visible_text(sentence)
    if not normalized:
        raise ValueError("readability finding normalized sentence is empty")
    return {
        "finding_id": _readability_sha256(
            finding["finding_id"], label="readability finding identity"
        ),
        "band": copy.deepcopy(finding["band"]),
        "words": copy.deepcopy(finding["words"]),
        "kind": copy.deepcopy(finding["kind"]),
        "normalized_sentence": normalized,
    }


def readability_detector_contract_projection(
    detector_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind only the closed readability detector contract, not its inventory."""

    fields = {
        "schema_version",
        "detector_contract",
        "ordinary_target_words",
        "complex_target_words",
        "hard_max_words",
        "bullet_decision_max",
    }
    if (
        not isinstance(detector_contract, Mapping)
        or set(detector_contract) != fields
        or detector_contract.get("schema_version") != 2
        or detector_contract.get("detector_contract") != "ai-readability-v1"
        or any(
            type(detector_contract.get(field)) is not int
            or detector_contract[field] < 1
            for field in (
                "ordinary_target_words",
                "complex_target_words",
                "hard_max_words",
            )
        )
        or detector_contract.get("bullet_decision_max") != 1
    ):
        raise ValueError("readability detector contract is invalid")
    return {
        "contract_id": READABILITY_DETECTOR_CONTRACT_ID,
        "detector_contract": copy.deepcopy(dict(detector_contract)),
    }


def actionability_detector_contract_projection(
    *, score_threshold: int, front_window_lines: int
) -> dict[str, Any]:
    """Bind the closed actionability selection and evidence-window policy."""

    if (
        type(score_threshold) is not int
        or score_threshold < 1
        or type(front_window_lines) is not int
        or front_window_lines
        != READABILITY_ACTIONABILITY_FRONT_WINDOW_UNIT_LIMIT
    ):
        raise ValueError("actionability detector contract thresholds are invalid")
    return {
        "contract_id": ACTIONABILITY_DETECTOR_CONTRACT_ID,
        "selection": (
            "actionability-applicable-iff-weak-front-loaded-action-reason"
        ),
        "target_identity": "sha256-actionability-target-v1-path",
        "source": "canonical-root-body-normalized-logical-unit-front-window",
        "window_unit": READABILITY_LOGICAL_UNIT_CONTRACT_ID,
        "score_threshold": score_threshold,
        "front_window_unit_limit": front_window_lines,
    }


def semantic_disposition_contract_projection() -> dict[str, Any]:
    """Return the closed Semantic currentness and authority-selection rules."""

    return copy.deepcopy(SEMANTIC_DISPOSITION_CONTRACT_PROJECTION)


def semantic_detector_compatibility_rows() -> list[dict[str, Any]]:
    """Return the single pinned source-only detector migration row."""

    return copy.deepcopy(list(_SEMANTIC_DETECTOR_COMPATIBILITY_ROWS))


def semantic_disposition_contract_fingerprint(
    projection: Mapping[str, Any] | None = None,
) -> str:
    """Return the canonical digest of the Semantic-only review contract."""

    value: object = (
        SEMANTIC_DISPOSITION_CONTRACT_PROJECTION
        if projection is None
        else projection
    )
    return canonical_json_sha256(value)


def _semantic_contract_projection() -> dict[str, Any]:
    return {
        "contract_version": PROFESSIONAL_SCHEMA3_CONTRACT_VERSION,
        "artifact_contract": {
            "schema_version": PROFESSIONAL_SCHEMA3_SCHEMA_VERSION,
            "kinds": {
                "packet": PROFESSIONAL_PACKET_KIND,
                "ballot": PROFESSIONAL_BALLOT_KIND,
                "decision": PROFESSIONAL_DECISION_KIND,
                "discovery_capsule": PROFESSIONAL_DISCOVERY_CAPSULE_KIND,
                "candidate_request": PROFESSIONAL_CANDIDATE_REQUEST_KIND,
                "review_capsule": PROFESSIONAL_REVIEW_CAPSULE_KIND,
            },
            "currentness_digest": "sha256-canonical-explicit-semantic-projection",
            "current_review_contract_field": "review_contract_fingerprint",
            "current_source_fingerprints_allowed": False,
        },
        "panel": {
            "decision_method": PROFESSIONAL_INCREMENTAL_DECISION_METHOD,
            "exact_votes_per_target": PROFESSIONAL_PANEL_SIZE,
            "minimum_winning_votes": PROFESSIONAL_MINIMUM_WINNING_VOTES,
            "abstentions_allowed": False,
            "independent_ballots": True,
            "fresh_reviewer_pool_minimum": PROFESSIONAL_PANEL_SIZE,
            "all_carry_reviewer_pool_size": 0,
            "assignments_non_empty_when_fresh": True,
            "unique_voter_and_agent_per_round": True,
            "fixed_pool_size": False,
        },
        "criteria": {
            "definitions": dict(sorted(PROFESSIONAL_CRITERIA.items())),
            "domain_critical": sorted(PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA),
            "ordinary": sorted(PROFESSIONAL_ORDINARY_CRITERIA),
            "values": sorted(PROFESSIONAL_CRITERION_VALUES),
            "review_outcomes": sorted(PROFESSIONAL_REVIEW_OUTCOMES),
            "adjacency_dispositions": sorted(PROFESSIONAL_ADJACENCY_DISPOSITIONS),
            "decisions": sorted(PROFESSIONAL_DECISIONS),
            "final_dispositions": sorted(PROFESSIONAL_FINAL_DISPOSITIONS),
            "reason_codes": {
                disposition: sorted(reason_codes)
                for disposition, reason_codes in sorted(
                    PROFESSIONAL_REASON_CODES.items()
                )
            },
            "qualified_domain_defect_disposition": (
                PROFESSIONAL_UNRESOLVED_DISPOSITION
            ),
            "domain_defect_arbitration_supported": False,
            "ordinary_defect_votes_required": PROFESSIONAL_MINIMUM_WINNING_VOTES,
            "ordinary_correction_disposition": (
                PROFESSIONAL_CORRECTION_DISPOSITION
            ),
            "overall_ballot_majority_usage": "audit-only",
        },
        "qualification": {
            "required_domain_experts_per_target": (
                PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
            ),
            "required_architecture_experts_per_target": (
                PROFESSIONAL_REQUIRED_ARCHITECTURE_EXPERTS
            ),
            "architecture_expertise_tag": (
                PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
            ),
            "architecture_tag_must_be_only_tag": True,
            "domain_tags_cover_all_target_tags": True,
            "claims_exactly_cover_reviewer_tags": True,
            "claims_are_static_and_do_not_prove_identity_or_experience": True,
        },
        "carry_origin_lineage": {
            "algorithm": "exact-package-carry-forward-v1",
            "bootstrap_requires_all_fresh": True,
            "legacy_baseline_allowed": False,
            "carry": copy.deepcopy(PROFESSIONAL_CARRY_CONTRACT),
            "origin_mode": "direct-last-fresh-decision",
            "maximum_origin_depth": 1,
            "maximum_plan_lineage_depth": (
                PROFESSIONAL_MAXIMUM_PLAN_LINEAGE_DEPTH
            ),
            "lineage_limit_disposition": "full-fresh-checkpoint",
            "stale_contract_baseline_policy": (
                "audit-envelope-only-force-full-fresh-v1"
            ),
            "carried_target_votes_allowed": False,
            "carried_target_effective_qualification_source": (
                "validated-direct-fresh-origin"
            ),
            "maintainer_partition_override_allowed": False,
            "capsule_chain": (
                "discovery-capsule-to-immutable-candidate-request-to-final-review-capsule"
            ),
            "discovery_capsule": copy.deepcopy(
                PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
            ),
            "review_capsule": copy.deepcopy(PROFESSIONAL_REVIEW_CAPSULE_CONTRACT),
        },
        "binding_contracts": {
            "target_version": PROFESSIONAL_TARGET_BINDING_CONTRACT_VERSION,
            "currentness_projection": copy.deepcopy(
                PROFESSIONAL_CURRENTNESS_PROJECTION_CONTRACT
            ),
            "target_fields": sorted(PROFESSIONAL_TARGET_BINDING_FIELDS),
            "snapshot_target_fields": sorted(PROFESSIONAL_SNAPSHOT_TARGET_FIELDS),
            "material_record_fields": sorted(PROFESSIONAL_MATERIAL_RECORD_FIELDS),
            "registry_authority_required_fields": sorted(
                PROFESSIONAL_REGISTRY_AUTHORITY_REQUIRED_FIELDS
            ),
            "reference_authority_fields": sorted(
                PROFESSIONAL_REFERENCE_AUTHORITY_FIELDS
            ),
            "adjacency_binding_fields": sorted(
                PROFESSIONAL_ADJACENCY_REVIEW_BINDING_FIELDS
            ),
            "required_candidate_material_binding_fields": sorted(
                PROFESSIONAL_REQUIRED_CANDIDATE_MATERIAL_BINDING_FIELDS
            ),
            "dependency_version": (
                PROFESSIONAL_DEPENDENCY_BINDING_CONTRACT_VERSION
            ),
            "dependency_fields": sorted(
                PROFESSIONAL_DECISION_DEPENDENCY_FIELDS
            ),
            "dependency_depth": "one-hop-material-review-authority",
            "dependency_union": (
                "packet-required-plus-reviewer-added-candidate-union"
            ),
            "fresh_state_is_not_transitive_dependency": True,
            "compact_authority_version": (
                PROFESSIONAL_COMPACT_AUTHORITY_CONTRACT_VERSION
            ),
            "compact_authority_fields": sorted(
                PROFESSIONAL_COMPACT_AUTHORITY_FIELDS
            ),
            "currentness_scope": (
                "target-local-conservative-required-and-authenticated-"
                "reviewer-added-v6"
            ),
            "content_fingerprint": (
                "raw-package-provenance-integrity-only-not-currentness"
            ),
            "fresh_review_context_is_currentness_authority": False,
            "compact_storage": {
                "schema_version": 2,
                "dependency_material_catalog": (
                    "top-level-dependency-id-to-material-review-binding"
                ),
                "finding_authority": [
                    "package_material_binding",
                    "review_unit_binding",
                    "dependency_ids",
                ],
                "legacy_aliases_allowed": False,
            },
        },
        "adjacency": {
            "algorithm": PROFESSIONAL_ADJACENCY_ALGORITHM,
            "selection_version": PROFESSIONAL_ADJACENCY_SELECTION_VERSION,
            "overall_top_k": PROFESSIONAL_ADJACENCY_TOP_K,
            "per_signal_top_k": PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K,
            "layered_signals": list(PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS),
            "signal_weights": dict(sorted(PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS.items())),
            "per_signal_order": [
                "signal-count-desc",
                "total-score-desc",
                "skill-id-asc",
            ],
            "require_all_registry_declared": True,
            "require_all_source_declared": True,
            "source_declared_version": (
                PROFESSIONAL_SOURCE_DECLARED_SELECTION_VERSION
            ),
            "source_declared_direction": "target-to-candidate",
            "source_declared_materials": ["root", "indexed-references"],
            "source_declared_identity": "exact-inline-code-span-skill-id",
            "source_declared_contexts": list(PROFESSIONAL_SOURCE_DECLARED_CONTEXTS),
            "source_declared_excluded_surfaces": list(
                PROFESSIONAL_SOURCE_DECLARED_EXCLUDED_SURFACES
            ),
            "source_declared_unknown_or_self": "fail-closed",
            "negative_route_match_version": (
                PROFESSIONAL_NEGATIVE_ROUTE_MATCH_VERSION
            ),
            "negative_route_minimum_overlap_tokens": (
                PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS
            ),
            "require_all_negative_route_conflicts": True,
            "maximum_required_candidates_per_target": (
                PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
            ),
            "total_budget_derivation": {
                "rounding": "floor",
                "baseline_target_count": (
                    PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT
                ),
                "baseline_maximum_required_candidates_total": (
                    PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL
                ),
            },
            "maximum_document_frequency_percent": (
                PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT
            ),
            "reviewer_added_candidates": {
                "allowed": True,
                "source": "full-catalog-ranking",
                "discovery_reason_required": True,
            },
            "adjacency_stop_words": sorted(PROFESSIONAL_ADJACENCY_STOP_WORDS),
            "negative_route_generic_tokens": sorted(
                PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS
            ),
        },
        "evidence": {
            "contract_versions": {
                "anchor_binding": "professional-evidence-anchor-binding-v1",
                "phrase_grounding": "schema3-contiguous-source-grounding-v1",
                "proof_limits": "professional-proof-limits-required-v1",
                "uniform_template_guard": "schema3-uniform-template-guard-v1",
                "defect_consistency_guard": "schema3-defect-consistency-v1",
            },
            "criterion_source_anchors_required": True,
            "all_anchors_must_be_used": True,
            "minimum_failure_modes_per_target": PROFESSIONAL_MINIMUM_EXAMINED_ITEMS,
            "minimum_omission_candidates_per_target": (
                PROFESSIONAL_MINIMUM_EXAMINED_ITEMS
            ),
            "minimum_assertion_overlap_tokens": (
                PROFESSIONAL_MINIMUM_ASSERTION_OVERLAP_TOKENS
            ),
            "minimum_examined_item_overlap_tokens": (
                PROFESSIONAL_MINIMUM_EXAMINED_ITEM_OVERLAP_TOKENS
            ),
            "minimum_adjacency_side_overlap_tokens": (
                PROFESSIONAL_MINIMUM_ADJACENCY_SIDE_OVERLAP_TOKENS
            ),
            "adjacency_candidate_coverage_required": True,
            "proof_limits_required": True,
            "evidence_stop_words": sorted(PROFESSIONAL_EVIDENCE_STOP_WORDS),
            "grounding_stop_words": sorted(PROFESSIONAL_GROUNDING_STOP_WORDS),
            "semantic_grounding": copy.deepcopy(
                PROFESSIONAL_SEMANTIC_GROUNDING_CONTRACT
            ),
            "defect_consistency": {
                "failure_defect_matches_failure_criterion": True,
                "omission_defect_matches_omission_criterion": True,
                "adjacency_defect_matches_adjacency_criterion": True,
                "vote_decision_matches_any_criterion_defect": True,
                "architecture_cannot_assert_domain_critical_defect": True,
                "qualified_domain_critical_defect_fails_closed": True,
            },
        },
        "compact_vote_projection": {
            "contract_version": PROFESSIONAL_COMPACT_VOTE_CONTRACT_VERSION,
            "exact_votes_per_target": PROFESSIONAL_PANEL_SIZE,
            "fields": sorted(PROFESSIONAL_COMPACT_VOTE_FIELDS),
            "criteria_fields": sorted(PROFESSIONAL_COMPACT_CRITERIA_FIELDS),
            "ordinary_criteria": sorted(PROFESSIONAL_ORDINARY_CRITERIA),
            "domain_critical_defect_criteria": sorted(
                PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
            ),
            "collection_fields": sorted(PROFESSIONAL_COMPACT_COLLECTION_FIELDS),
            "adjacency_fields": sorted(PROFESSIONAL_COMPACT_ADJACENCY_FIELDS),
            "proof_limit_fields": sorted(
                PROFESSIONAL_COMPACT_PROOF_LIMIT_FIELDS
            ),
            "proof_limit_item_maximum": (
                PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_MAXIMUM
            ),
            "proof_limit_item_count": (
                PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_COUNT
            ),
            "rationale_maximum": PROFESSIONAL_COMPACT_RATIONALE_MAXIMUM,
            "review_evidence_fingerprint": "canonical-full-voter-and-vote",
            "collection_summaries_retain_count_defect-count-and-digest": True,
            "adjacency_summary_retains_required-and-reviewer-added_identity": True,
            "proof_summary_retains_bounded-leading-items": True,
            "authenticated_projection_requires_exact_authority_match": True,
        },
    }


PROFESSIONAL_SCHEMA3_CONTRACT_PROJECTION = _semantic_contract_projection()


def professional_schema3_contract_projection() -> dict[str, Any]:
    """Return a detached semantic projection suitable for canonical hashing."""

    return copy.deepcopy(PROFESSIONAL_SCHEMA3_CONTRACT_PROJECTION)


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes for one semantic projection."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    """Return the canonical SHA-256 for one JSON-compatible value."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def semantic_disposition_record_fingerprint(axis: str, entry: object) -> str:
    """Bind one config decision record independently from current source evidence."""

    if axis not in {"root", "reference"} or not isinstance(entry, dict):
        raise ValueError("semantic disposition record input is invalid")
    projection = {
        key: copy.deepcopy(value)
        for key, value in entry.items()
        if key != "record_fingerprint"
    }
    return hashlib.sha256(
        f"{SEMANTIC_DISPOSITION_RECORD_VERSION}:{axis}".encode("utf-8")
        + b"\0"
        + canonical_json_bytes(projection)
    ).hexdigest()


def professional_review_contract_fingerprint(
    projection: Mapping[str, Any] | None = None,
) -> str:
    """Return the current Professional semantic review/carry digest."""

    value: object = (
        PROFESSIONAL_SCHEMA3_CONTRACT_PROJECTION
        if projection is None
        else projection
    )
    return canonical_json_sha256(value)
