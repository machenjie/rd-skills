from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
OLD_RECORD = {
    "name": "Ada",
    "email": "ada@example.test",
    "phone": "+1-555-0100",
    "marketing": False,
}


def load_subject():
    path = ROOT / "profile_api.py"
    spec = importlib.util.spec_from_file_location("candidate_profile_api", path)
    if spec is None or spec.loader is None:
        raise AssertionError("profile_api.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackwardCompatibleApiFieldAssertions(unittest.TestCase):
    def test_old_rows_and_omitted_patch_field_remain_compatible(self) -> None:
        subject = load_subject()
        response = subject.serialize_profile(dict(OLD_RECORD))
        self.assertEqual(response["preferred_contact_method"], None)
        self.assertEqual(
            {key: response[key] for key in OLD_RECORD},
            OLD_RECORD,
        )
        self.assertEqual(subject.patch_profile(dict(OLD_RECORD), {"name": "Ada L."})["name"], "Ada L.")

    def test_new_values_are_validated_without_mutating_input_on_failure(self) -> None:
        subject = load_subject()
        for value in ("email", "phone", "sms", None):
            original = dict(OLD_RECORD)
            updated = subject.patch_profile(original, {"preferred_contact_method": value})
            self.assertEqual(updated["preferred_contact_method"], value)
            self.assertEqual(original, OLD_RECORD)
        original = dict(OLD_RECORD)
        with self.assertRaises(ValueError):
            subject.patch_profile(original, {"preferred_contact_method": "fax"})
        self.assertEqual(original, OLD_RECORD)

    def test_schema_is_additive_and_nullable(self) -> None:
        schema = json.loads((ROOT / "profile_schema.json").read_text(encoding="utf-8"))
        self.assertNotIn("preferred_contact_method", schema["required"])
        self.assertEqual(
            set(schema["properties"]["preferred_contact_method"]["enum"]),
            {"email", "phone", "sms", None},
        )
        self.assertEqual(set(schema["required"]), set(OLD_RECORD))


if __name__ == "__main__":
    unittest.main()
