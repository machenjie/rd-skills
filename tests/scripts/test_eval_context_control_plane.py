"""Consumers reject stale or inconsistent producer evidence without replaying it."""
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('context_eval', ROOT / 'scripts/eval-context-control-plane.py')
EVAL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EVAL)


def reports():
    ids = ['isolated-write-parallel-contract', 'shared-workspace-serial-write']
    source = dict(schema_version=2, fixture_schema_version=2, status='pass', errors=[],
                  evidence_scope='deterministic-fixtures', fixture_count=len(ids),
                  cases=[dict(id=id, errors=[], matches_expected=True, metrics={}) for id in ids],
                  negative_cases=[dict(id='overlapping-shared-write', errors=['write conflict'], matches_expected=True)],
                  aggregate_structural_proxies={'subagent_count': {'max': 2}},
                  limitations=['Simulated fixtures do not prove real Host behavior.'])
    rendered = dict(schema_version=2, fixture_schema_version=2, status='pass', errors=[],
                    evidence_scope='deterministic-rendered-artifacts', fixture_count=len(ids),
                    cases=[dict(id=id) for id in ids], tokenizer='o200k_base',
                    hosts=['codex', 'claude', 'copilot'], aggregate={'max_main': {'tokens': 1000}},
                    limitations=['Measured artifact tokens do not prove wall-clock performance.'])
    return source, rendered


class ContextConsumerTests(unittest.TestCase):
    def invoke(self, source=None, rendered=None, *, missing=None):
        good_source, good_rendered = reports()
        source = good_source if source is None else source
        rendered = good_rendered if rendered is None else rendered
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, value in [('hookless-control-plane-eval.json', source), ('rendered-context-budget.json', rendered)]:
                if name != missing:
                    (root / name).write_text(json.dumps(value))
            with mock.patch.object(subprocess, 'run', side_effect=AssertionError('must consume, not replay')):
                return EVAL.evaluate(root)

    def test_passes_and_copies_real_producer_measurements(self):
        source, rendered = reports()
        result = self.invoke(source, rendered)
        self.assertEqual('pass', result['status'])
        self.assertEqual(rendered['aggregate'], result['rendered_context_summary'])
        self.assertEqual(source['aggregate_structural_proxies'], result['structural_proxies'])
        self.assertEqual(source['limitations'] + rendered['limitations'], result['limitations'])

    def test_rejects_missing_producer_without_launching_it(self):
        for name in ['hookless-control-plane-eval.json', 'rendered-context-budget.json']:
            with self.subTest(name=name), self.assertRaises(OSError):
                self.invoke(missing=name)

    def test_rejects_failed_wrong_scope_or_old_schema_producer(self):
        for side in range(2):
            for key, value in [('status', 'fail'), ('errors', ['defect']), ('schema_version', 1), ('evidence_scope', 'live-host')]:
                values = list(reports()); values[side][key] = value
                with self.subTest(side=side, key=key), self.assertRaises(ValueError):
                    self.invoke(*values)

    def test_rejects_mismatched_or_duplicate_fixture_identity(self):
        source, rendered = reports()
        rendered['cases'][0]['id'] = 'wrong-subject'
        self.assertEqual('fail', self.invoke(source, rendered)['status'])
        rendered['cases'][0]['id'] = rendered['cases'][1]['id']
        with self.assertRaises(ValueError):
            self.invoke(source, rendered)

    def test_requires_real_negative_controls_and_passing_positive_cases(self):
        for mutate in [lambda s: s.update(negative_cases=[]),
                       lambda s: s['negative_cases'][0].update(errors=[]),
                       lambda s: s['cases'][0].update(errors=['write conflict']),
                       lambda s: s['cases'][0]['metrics'].update(parallel_write_conflict=True)]:
            source, rendered = reports(); mutate(source)
            self.assertEqual('fail', self.invoke(source, rendered)['status'])

    def test_requires_matching_fixture_schema_exact_tokens_and_all_hosts(self):
        for key, value in [('fixture_schema_version', 1), ('tokenizer', 'estimate'), ('hosts', ['codex'])]:
            source, rendered = reports(); rendered[key] = value
            self.assertEqual('fail', self.invoke(source, rendered)['status'])

    def test_missing_report_cli_returns_failure_without_output(self):
        with tempfile.TemporaryDirectory() as raw, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, EVAL.main(['--reports-dir', raw]))
            self.assertFalse((Path(raw) / 'context-control-plane-eval.json').exists())


if __name__ == '__main__':
    unittest.main()
