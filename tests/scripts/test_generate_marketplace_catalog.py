from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-marketplace-catalog.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_marketplace_catalog", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateMarketplaceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.payload = cls.module.generate_catalog(ROOT)
        cls.rendered = cls.module.render_catalog(cls.payload)

    def test_catalog_is_derived_from_v3_exported_indexes(self) -> None:
        self.assertEqual(len(self.payload["index"]["items"]), 190)
        self.assertEqual(len(self.payload["items"]), 190)
        self.assertEqual(
            self.payload["index"]["schema_version"],
            3,
        )
        self.assertIn("engineering-control-plane", self.payload["items"])
        self.assertIn("backend-change-builder", self.payload["items"])
        self.assertIn("transaction-consistency", self.payload["items"])

    def test_rendered_catalog_has_new_architecture_sections(self) -> None:
        for section in (
            "## How To Use This Catalog",
            "## Quick Navigation",
            "## Runtime Summary",
            "## Control Skills",
            "## Professional Skills",
            "## Foundation Skills By Group",
            "## Domain Skills",
            "## Browse By Agent Profile",
            "## Browse By Trigger Signal",
            "## Browse By Runtime Delivery",
        ):
            self.assertIn(section, self.rendered)
        self.assertIn("| `recommended` | 27 | 154 | 9 |", self.rendered)
        self.assertNotIn("| `full` |", self.rendered)
        self.assertNotIn("| `dev` |", self.rendered)
        self.assertIn("### `engineering-control-plane`", self.rendered)
        self.assertIn("### `backend-change-builder`", self.rendered)
        self.assertIn("#### `transaction-consistency`", self.rendered)
        self.assertIn("- Task routable: `true`", self.rendered)
        self.assertIn("- Runtime delivery:", self.rendered)
        self.assertIn("Marketplace schema v3 discovery view", self.rendered)
        self.assertIn(
            "Official marketplace publishing is intentionally not implemented",
            self.rendered,
        )

    def test_large_browse_groups_are_split_into_short_lists(self) -> None:
        agent_browse = self.rendered.split(
            "## Browse By Agent Profile", 1
        )[1].split("## Browse By Trigger Signal", 1)[0]
        delivery_browse = self.rendered.split(
            "## Browse By Runtime Delivery", 1
        )[1]

        self.assertIn("### `task-agent`", agent_browse)
        self.assertIn("### `top_level_skill`", delivery_browse)
        for section in (agent_browse, delivery_browse):
            name_lines = [line for line in section.splitlines() if line.startswith("- `")]
            self.assertTrue(name_lines)
            self.assertLessEqual(max(line.count("`, `") + 1 for line in name_lines), 3)
            self.assertLess(max(map(len, name_lines)), 200)

    def test_generated_markdown_avoids_unreadable_long_lines(self) -> None:
        long_lines = [
            (number, len(line))
            for number, line in enumerate(self.rendered.splitlines(), start=1)
            if len(line) > 200
        ]

        self.assertEqual([], long_lines)

    def test_wrapping_preserves_hyphenated_tokens_and_inline_code(self) -> None:
        split_hyphenated_tokens = [
            (number, line)
            for number, line in enumerate(self.rendered.splitlines(), start=1)
            if line.rstrip().endswith("-")
        ]
        unbalanced_inline_code = [
            (number, line)
            for number, line in enumerate(self.rendered.splitlines(), start=1)
            if line.count("`") % 2
        ]

        self.assertEqual([], split_hyphenated_tokens)
        self.assertEqual([], unbalanced_inline_code)
        for token in (
            "`task-agent`",
            "`review-agent`",
            "no-repo",
            "cross-context",
            "authentication-to-authorization",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.rendered)

    def test_every_registry_item_remains_discoverable(self) -> None:
        for name in self.payload["items"]:
            with self.subTest(name=name):
                self.assertIn(f"`{name}`", self.rendered)

    def test_rendered_catalog_has_no_obsolete_pack_metadata(self) -> None:
        for marker in (
            ".changeforge-packs",
            "JIT agent packs",
            "specialist pack",
            "review pack",
            "runtime_path",
            "dev-only",
        ):
            self.assertNotIn(marker, self.rendered)

    def test_check_mode_catches_stale_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "MARKETPLACE_CATALOG.md"
            out.write_text("stale\n", encoding="utf-8")
            self.assertEqual(
                self.module.main(
                    ["--check", "--out", str(out)]
                ),
                1,
            )

    def test_check_mode_accepts_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "MARKETPLACE_CATALOG.md"
            self.assertEqual(
                self.module.main(["--out", str(out)]),
                0,
            )
            self.assertEqual(
                self.module.main(["--check", "--out", str(out)]),
                0,
            )

    def test_obsolete_profile_argument_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as caught:
                self.module.main(
                    ["--profile", "dev", "--out", str(Path(tmp) / "catalog.md")]
                )
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
