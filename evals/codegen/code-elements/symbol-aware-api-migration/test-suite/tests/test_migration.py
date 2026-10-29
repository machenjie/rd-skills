import importlib.util
import os
import unittest
from pathlib import Path
from types import SimpleNamespace


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(source):
    """Independent fictional APIs expose default, error, and cleanup semantics."""
    events = []
    def old_fetch(key: str, *, strict=True, release=True) -> str:
        events.append("acquire")
        try:
            events.append("read")
            if key == "missing" and strict:
                raise LookupError(key)
            return "" if key == "missing" else "value:" + key
        finally:
            if release:
                events.append("close")
    def new_fetch(key: str, *, strict=False, release=False) -> str:
        return old_fetch(key, strict=strict, release=release)
    modules = {"legacy_api": SimpleNamespace(fetch=old_fetch),
               "current_api": SimpleNamespace(fetch=new_fetch),
               "other_api": SimpleNamespace(fetch=lambda key: "other:" + key)}
    def importer(name, *args, **kwargs):
        return modules[name]
    namespace = {"__builtins__": {"__import__": importer}}
    error = None
    try:
        exec(compile(source, "fixture.py", "exec"), namespace)
    except LookupError as failure:
        error = (type(failure).__name__, str(failure))
    return namespace.get("result"), events, error, (old_fetch.__annotations__, new_fetch.__annotations__)


class MigrationAssertions(unittest.TestCase):
    def test_symbol_identity_aliases_comments_and_strings(self):
        source = ('import legacy_api as old\nimport other_api as other\n'
                  'from legacy_api import fetch as renamed\n'
                  '# old.fetch("comment")\nlabel = "old.fetch(string)"\n'
                  'unrelated = other.fetch("a")\n'
                  'result = (old.fetch("a"), renamed("b"), unrelated)\n')
        result = subject().migrate(source)
        self.assertEqual(result["changed_calls"], 2)
        self.assertEqual(result["unresolved"], [])
        self.assertIn('# old.fetch("comment")\nlabel = "old.fetch(string)"', result["source"])
        self.assertIn('unrelated = other.fetch("a")', result["source"])
        self.assertEqual(execute(result["source"]), execute(source))

    def test_utf8_offsets_and_trailing_comma(self):
        source = 'import legacy_api as old\nlabel = "€"; result = old.fetch("a",)  # 保留\n'
        result = subject().migrate(source)
        self.assertEqual(result["changed_calls"], 1)
        self.assertIn('label = "€";', result["source"])
        self.assertTrue(result["source"].endswith('  # 保留\n'))
        self.assertEqual(execute(result["source"]), execute(source))

    def test_compilation_and_equal_types_do_not_prove_behavior(self):
        for key in ("a", "missing"):
            with self.subTest(key=key):
                source = 'import legacy_api as api\nresult = api.fetch(' + repr(key) + ')\n'
                before = execute(source)
                naive = source.replace("legacy_api", "current_api")
                after_naive = execute(naive)
                self.assertEqual(before[3][0], before[3][1])
                self.assertNotEqual(before[:3], after_naive[:3])
                migrated = subject().migrate(source)
                self.assertEqual(execute(migrated["source"]), before)
                self.assertIn("strict=True", migrated["source"])
                self.assertIn("release=True", migrated["source"])

    def test_explicit_policy_is_preserved(self):
        source = 'from legacy_api import fetch\nresult = fetch("missing", strict=False, release=False)\n'
        result = subject().migrate(source)
        self.assertEqual(result["changed_calls"], 1)
        self.assertEqual(execute(result["source"]), execute(source))
        self.assertNotIn("strict=True", result["source"])
        self.assertEqual(result["residual_import_lines"], [])

    def test_shadowed_bindings_return_unchanged_for_judgment(self):
        samples = [
            'import legacy_api as api\ndef run(api):\n    return api.fetch("a")\n',
            'from legacy_api import fetch\ndef run():\n    fetch = other\n    return fetch("a")\n',
            'import legacy_api as api\napi = other\nresult = api.fetch("a")\n',
        ]
        for source in samples:
            with self.subTest(source=source):
                result = subject().migrate(source)
                self.assertEqual(result["source"], source)
                self.assertEqual(result["changed_calls"], 0)
                self.assertTrue(result["unresolved"])
                self.assertEqual(result["residual_import_lines"], [1])

    def test_reexport_dynamic_call_and_mixed_residual_scan(self):
        for tail in ('public_fetch = old.fetch\n', 'result = old.fetch("a", **options)\n'):
            source = 'import legacy_api as old\nimport current_api as new\n' + tail
            result = subject().migrate(source)
            self.assertEqual(result["source"], source)
            self.assertTrue(result["unresolved"])
            self.assertEqual(result["residual_import_lines"], [1])
            self.assertTrue(result["mixed"])

    def test_repeat_is_idempotent_and_invalid_input_is_not_changed(self):
        source = ('import legacy_api as old\nimport current_api as new\n'
                  'result = old.fetch("a")\nexisting = new.fetch("a")\n')
        first = subject().migrate(source)
        second = subject().migrate(first["source"])
        self.assertEqual(first["changed_calls"], 1)
        self.assertEqual(first["source"], second["source"])
        self.assertEqual(second["changed_calls"], 0)
        self.assertEqual(second["residual_import_lines"], [])
        self.assertFalse(second["mixed"])
        self.assertIn('existing = new.fetch("a")', second["source"])
        invalid = 'import legacy_api as old\nresult = old.fetch(\n'
        with self.assertRaises(ValueError):
            subject().migrate(invalid)
        self.assertTrue(invalid.endswith('old.fetch(\n'))
