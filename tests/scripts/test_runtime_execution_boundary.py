"""Write boundary and genuine tool/diff evidence; reads may discover new owners."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import validation_utils as V


class RuntimeBoundaryTests(unittest.TestCase):
    def test_segment_globs_do_not_expand_write_authority(self):
        self.assertTrue(V._target_in_task_scope('src/owner.py', ['src/*.py'], ROOT))
        self.assertFalse(V._target_in_task_scope('src/nested/owner.py', ['src/*.py'], ROOT))
        self.assertTrue(V._target_in_task_scope('src/nested/owner.py', ['src/**/*.py'], ROOT))
        self.assertTrue(V._target_in_task_scope('src/owner.py', ['src/**/*.py'], ROOT))

    def test_parent_and_absolute_escape_are_rejected(self):
        for target in ('src/../private.py', '/tmp/private.py'):
            self.assertFalse(V._target_in_task_scope(target, ['src/*'], ROOT))

    def test_symlink_cannot_expand_write_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'src').mkdir(); (root / 'other').mkdir()
            (root / 'src/link').symlink_to(root / 'other', target_is_directory=True)
            self.assertFalse(V._target_in_task_scope('src/link/private.py', ['src/**'], root))

    def test_blocker_is_syntax_not_self_proof(self):
        text = V.format_execution_blocker(task_id='test-task', operation='read', observed='Host denied target read')
        self.assertIn('Host denied target read', text)
        with self.assertRaises(ValueError):
            V.format_execution_blocker(task_id='unspecified', operation='read', observed='claimed failure')

    def test_exact_diff_is_distinct_from_summary(self):
        patch = 'diff --git a/src/owner.py b/src/owner.py\n--- a/src/owner.py\n+++ b/src/owner.py\n@@ -1 +1 @@\n-return None\n+return []\n'
        self.assertEqual(['src/owner.py'], V.unified_diff_paths(patch))
        self.assertIsNone(V.unified_diff_paths('Changed owner.py and tests passed'))


if __name__ == '__main__':
    unittest.main()
