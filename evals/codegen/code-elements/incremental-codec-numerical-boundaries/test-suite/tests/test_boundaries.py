import importlib.util
import copy
from decimal import Decimal, localcontext
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

    def test_rod_model_agrees_with_independent_analytic_dirichlet_solution(self):
        candidate = subject()
        for length, conductivity, count in ((1.0, 1.0, 3), (2.0, 3.0, 5), (4.0, 2.0, 9)):
            problem = {"length_m": length, "conductivity": conductivity, "heat_source": 0.0,
                       "left": {"kind": "temperature", "value": 300.0},
                       "right": {"kind": "temperature", "value": 400.0}}
            coordinates = [index * length / (count - 1) for index in range(count)]
            analytic = [300.0 + (400.0 - 300.0) * coordinate / length for coordinate in coordinates]
            with self.subTest(length=length, count=count):
                result = candidate.rod_evidence(problem, analytic)
                self.assertEqual(result, {"residual": 0.0, "numerical_pass": True,
                                          "applicable": True, "boundary_pass": True, "accepted": True})

    def test_zero_residual_cannot_validate_an_unsupported_source_or_wrong_boundary(self):
        candidate = subject()
        problem = {"length_m": 2.0, "conductivity": 3.0, "heat_source": 0.0,
                   "left": {"kind": "temperature", "value": 300.0},
                   "right": {"kind": "temperature", "value": 400.0}}
        temperatures = [300.0, 325.0, 350.0, 375.0, 400.0]
        sourced = copy.deepcopy(problem)
        sourced["heat_source"] = 6.0
        # Independent solution of k*T'' + q = 0 with these temperature endpoints.
        coordinate = 1.0
        true_midpoint = 350.0 + sourced["heat_source"] * coordinate * (2.0 - coordinate) / (2 * sourced["conductivity"])
        self.assertEqual(true_midpoint, 351.0)
        self.assertNotEqual(temperatures[2], true_midpoint)
        wrong_boundary = copy.deepcopy(problem)
        wrong_boundary["left"]["value"] = 310.0
        unsupported_boundary = copy.deepcopy(problem)
        unsupported_boundary["left"] = {"kind": "flux", "value": 0.0}
        for name, actual, applicable in (("source", sourced, False), ("endpoint", wrong_boundary, True),
                                          ("boundary-kind", unsupported_boundary, False)):
            with self.subTest(problem=name):
                result = candidate.rod_evidence(actual, temperatures)
                self.assertEqual(result["residual"], 0.0)
                self.assertTrue(result["numerical_pass"])
                self.assertEqual(result["applicable"], applicable)
                self.assertFalse(result["boundary_pass"])
                self.assertFalse(result["accepted"])

    def test_rod_numerical_error_and_invalid_physical_inputs_remain_rejected(self):
        candidate = subject()
        problem = {"length_m": 2.0, "conductivity": 3.0, "heat_source": 0.0,
                   "left": {"kind": "temperature", "value": 300.0},
                   "right": {"kind": "temperature", "value": 400.0}}
        result = candidate.rod_evidence(problem, [300.0, 325.0, 351.0, 375.0, 400.0])
        self.assertEqual(result["residual"], 24.0)
        self.assertFalse(result["numerical_pass"])
        self.assertTrue(result["applicable"])
        self.assertTrue(result["boundary_pass"])
        self.assertFalse(result["accepted"])
        tiny = {"length_m": 1e-162, "conductivity": 5e-324, "heat_source": 0,
                "left": {"kind": "temperature", "value": 300},
                "right": {"kind": "temperature", "value": 300}}
        with localcontext() as context:
            context.prec = 80
            # For [300, 300.125, 300], |second difference|=1/4 and dx=L/2.
            independent = Decimal.from_float(tiny["conductivity"]) / Decimal.from_float(tiny["length_m"]) ** 2
        self.assertGreater(independent, Decimal("4.9"))
        self.assertLess(independent, Decimal("5.0"))
        result = candidate.rod_evidence(tiny, [300, 300.125, 300])
        self.assertAlmostEqual(result["residual"], float(independent), places=12)
        self.assertFalse(result["numerical_pass"])
        self.assertFalse(result["accepted"])
        rounded = {**tiny, "length_m": 2}
        result = candidate.rod_evidence(rounded, [300, 300.125, 300], residual_budget=0)
        self.assertEqual(result["residual"], 0.0)
        self.assertFalse(result["numerical_pass"], "rounded zero cannot satisfy an exact zero budget")
        self.assertFalse(result["accepted"])
        overflow = {**tiny, "length_m": 2, "conductivity": 1e308}
        result = candidate.rod_evidence(overflow, [300, 302, 300])
        self.assertEqual(result["residual"], math.inf)
        self.assertFalse(result["numerical_pass"])
        self.assertFalse(result["accepted"])
        for key, value in (("length_m", 0), ("length_m", math.ulp(0.0)), ("conductivity", -1),
                           ("heat_source", math.inf), ("heat_source", 10 ** 1000)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "invalid rod evidence"):
                candidate.rod_evidence({**problem, key: value}, [300.0, 350.0, 400.0])
        with self.assertRaisesRegex(ValueError, "invalid rod evidence"):
            candidate.rod_evidence(problem, [300.0, 400.0])


if __name__ == "__main__":
    unittest.main()
