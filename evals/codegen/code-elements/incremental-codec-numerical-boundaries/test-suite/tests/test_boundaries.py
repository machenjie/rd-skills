import importlib.util
import math
import os
import unittest
from pathlib import Path


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BoundaryAssertions(unittest.TestCase):
    def test_every_partition_preserves_multibyte_frames(self):
        candidate = subject()
        wire = b"\x03\xe2\x82\xac\x01x"
        for left in range(len(wire) + 1):
            for right in range(left, len(wire) + 1):
                with self.subTest(left=left, right=right):
                    self.assertEqual(candidate.decode_frames([wire[:left], wire[left:right], wire[right:]]), (["€", "x"], "complete"))

    def test_split_varint_and_eof_have_distinct_outcomes(self):
        candidate = subject()
        self.assertEqual(candidate.decode_frames([b"\x80"], eof=False), ([], "need-more"))
        self.assertEqual(candidate.decode_frames([b"\x80", b"\x01", b"x" * 128]), (["x" * 128], "complete"))
        for payload in (b"\x80", b"\x03\xe2", b"\x80\x80\x80", b"\x01\xff"):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                candidate.decode_frames([payload])

    def test_declared_and_total_sizes_are_bounded(self):
        candidate = subject()
        for payload, limits in ((b"\x05", {"max_frame": 4}), (b"\x03abc\x03def", {"max_total": 5})):
            with self.assertRaises(ValueError):
                candidate.decode_frames([payload], **limits)
        self.assertEqual(candidate.decode_frames([b"\x00"]), ([""], "complete"))

    def test_partial_write_resumes_at_acknowledged_suffix(self):
        candidate = subject()
        calls, delivered = [], bytearray()
        def sink(data):
            calls.append(data)
            accepted = min(2, len(data))
            delivered.extend(data[:accepted])
            return accepted
        self.assertEqual(candidate.write_all(b"abcdef", sink), 6)
        self.assertEqual(calls, [b"abcdef", b"cdef", b"ef"])
        self.assertEqual(delivered, b"abcdef")
        with self.assertRaises(ValueError):
            candidate.write_all(b"x", lambda data: 0)

    def test_unit_shape_domain_and_precision_budget(self):
        candidate = subject()
        self.assertEqual(candidate.length_metres([3, 4, 0], "m"), 5)
        for values, unit in (([3, 4], "m"), ([3, 4, 0], "cm"), ([math.inf, 0, 0], "m"), ([math.nan, 0, 0], "m")):
            with self.assertRaises(ValueError):
                candidate.length_metres(values, unit)
        observed = candidate.length_metres([1e200, 1e200, 0], "m")
        self.assertTrue(math.isfinite(observed))
        self.assertLess(abs(observed / 1e200 - math.sqrt(2)), 1e-14)

    def test_unconverged_solver_cannot_report_success(self):
        candidate = subject()
        self.assertEqual(candidate.sqrt_result(4)[1], True)
        self.assertAlmostEqual(candidate.sqrt_result(4)[0], 2, places=10)
        self.assertEqual(candidate.sqrt_result(4, max_iterations=0)[1], False)
        with self.assertRaises(ValueError):
            candidate.sqrt_result(-1)

    def test_integer_allocation_conserves_total_over_finite_domain(self):
        candidate = subject()
        self.assertEqual(candidate.allocate(101, [1, 1, 1]), [34, 34, 33])
        for total in range(20):
            for a in range(1, 5):
                for b in range(1, 5):
                    result = candidate.allocate(total, [a, b])
                    self.assertEqual(sum(result), total)
                    self.assertTrue(all(isinstance(x, int) and x >= 0 for x in result))
                    self.assertEqual(result, candidate.allocate(total, [a, b]))
        with self.assertRaises(ValueError):
            candidate.allocate(10, [0, 0])


if __name__ == "__main__":
    unittest.main()
