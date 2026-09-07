#!/usr/bin/env python3
"""Consume current behavior and rendered context evidence without replaying producers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validation_utils import report_output_paths

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / 'reports/context-control-plane-eval.json'
REPORT_MD = ROOT / 'reports/context-control-plane-eval.md'


def _read_passing(path: Path, scope: str) -> dict:
    value = json.loads(path.read_text())
    if (value.get('schema_version') != 2 or value.get('status') != 'pass'
            or value.get('errors') != [] or value.get('evidence_scope') != scope):
        raise ValueError(f'{path.name}: current passing evidence with the expected scope is required')
    cases = value.get('cases')
    if not isinstance(cases, list) or not cases or value.get('fixture_count') != len(cases):
        raise ValueError(f'{path.name}: case/count mismatch')
    ids = [row.get('id') for row in cases]
    if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        raise ValueError(f'{path.name}: missing or duplicate case identity')
    return value


def evaluate(reports_dir: Path) -> dict:
    source = _read_passing(reports_dir / 'hookless-control-plane-eval.json', 'deterministic-fixtures')
    rendered = _read_passing(reports_dir / 'rendered-context-budget.json', 'deterministic-rendered-artifacts')
    errors = []
    if {row['id'] for row in source['cases']} != {row['id'] for row in rendered['cases']}:
        errors.append('rendered and behavior fixtures differ')
    if rendered.get('tokenizer') != 'o200k_base' or rendered.get('hosts') != ['codex', 'claude', 'copilot']:
        errors.append('exact tokens across all three built Hosts are required')
    if rendered.get('fixture_schema_version') != source.get('fixture_schema_version'):
        errors.append('fixture schema mismatch')
    by_id = {row['id']: row for row in source['cases']}
    for required in ('shared-workspace-serial-write', 'isolated-write-parallel-contract'):
        if required not in by_id or not by_id[required].get('matches_expected'):
            errors.append(f'missing passing write-boundary behavior: {required}')
    for row in source['cases']:
        if row.get('errors') or not row.get('matches_expected'):
            errors.append(f"{row['id']}: nonpassing behavior")
        metrics = row.get('metrics', {})
        if metrics.get('parallel_write_conflict') or metrics.get('preparation_loop_detected'):
            errors.append(f"{row['id']}: write conflict or repeated unsupported judgment")
    negatives = source.get('negative_cases', [])
    if not negatives or any(not row.get('errors') or not row.get('matches_expected') for row in negatives):
        errors.append('independent negative controls must reject concrete defects')
    host = json.loads((ROOT / 'src/agent-profiles/host-enforcement.json').read_text())
    if any(host['hosts'][name].get('isolated_workspace') != 'unsupported' for name in ('codex', 'claude', 'copilot')):
        errors.append('declared Hosts must not claim unobserved write isolation')
    core = json.loads((ROOT / 'src/control-model/core-contracts.json').read_text())
    producer = next(row for row in core['principle_acceptance_contract']['producers'] if row['id'] == 'eval-context-control')
    if producer['depends_on'] != ['eval-agent-lightweight', 'eval-rendered-context']:
        errors.append('context consumer dependencies must remain Core-owned')
    return {'schema_version': 2, 'status': 'pass' if not errors else 'fail',
            'evidence_scope': 'deterministic-fixtures', 'fixture_count': source['fixture_count'],
            'rendered_context_summary': rendered['aggregate'],
            'structural_proxies': source['aggregate_structural_proxies'],
            'limitations': list(dict.fromkeys(source['limitations'] + rendered['limitations'])), 'errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports-dir', type=Path, default=REPORT_JSON.parent)
    parser.add_argument('--release-projection', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.reports_dir)
    except (ValueError, OSError, KeyError) as exc:
        print(f'eval-context-control-plane: ERROR: {exc}')
        return 1
    out_json, out_md = report_output_paths(args.reports_dir, REPORT_JSON.name, REPORT_MD.name)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2) + '\n')
    if args.release_projection:
        out_md.write_text('# Context Control Plane\n\nStatus: ' + report['status'] + '\n\n' + '\n'.join('- '+s for s in report['limitations']) + '\n')
    for error in report['errors']:
        print('eval-context-control-plane: ERROR: ' + error)
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
