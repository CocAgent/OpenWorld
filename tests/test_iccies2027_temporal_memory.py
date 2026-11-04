"""Dependency-free correctness and negative controls for ICCIES 2027 study."""
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "benchmarks" / "iccies2027_temporal_memory.py"
spec = importlib.util.spec_from_file_location("iccies2027_temporal_memory", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TemporalMemoryTests(unittest.TestCase):
    def test_deterministic_and_no_duplicate_seed(self):
        self.assertEqual(m.tape("persist", 11, 120), m.tape("persist", 11, 120))
        with self.assertRaises(ValueError):
            m.run((11, 11))

    def test_marginal_does_not_preserve_time_order(self):
        a, b = m.Marginal(), m.Marginal()
        for y in (1, 1, 0, 0):
            a.observe(y)
        for y in (0, 1, 0, 1):
            b.observe(y)
        self.assertEqual(a.state(), b.state())
        self.assertEqual(a.predict(), b.predict())
        c, d = m.Conditional(), m.Conditional()
        for y in (1, 1, 0, 0):
            c.observe(y)
        for y in (0, 1, 0, 1):
            d.observe(y)
        self.assertNotEqual(c.state()["counts"], d.state()["counts"])

    def test_prequential_prediction_before_update(self):
        a = m.Marginal()
        self.assertAlmostEqual(a.predict(), 0.5)
        a.observe(1)
        self.assertAlmostEqual(a.predict(), 2/3)
        z = m.evaluate((1, 0, 1, 0), warmup=1)
        self.assertEqual(set(z), set(m.MODELS))

    def test_gate_never_receives_future(self):
        a, b = m.CostGate(), m.CostGate()
        for y in (1, 1, 0, 1, 0, 1):
            self.assertEqual(a.predict(), b.predict())
            a.observe(y)
            b.observe(y)
        self.assertEqual(a.state(), b.state())
        with self.assertRaises(ValueError):
            a.observe(True)

    def test_stochastic_dynamics_differ_despite_matched_stationary_marginals(self):
        # Both symmetric transition chains have uniform stationary marginals.
        self.assertNotEqual(m.tape("persist", 8, 120), m.tape("alternate", 8, 120))
        self.assertEqual(0.9 * 0.5 + 0.1 * 0.5, 0.5)
        self.assertEqual(0.1 * 0.5 + 0.9 * 0.5, 0.5)

    def test_reproducible_metrics_and_input_gates(self):
        r1 = m.run((15, 16), steps=80, warmup=20, scenarios=("persist", "iid_half"))
        r2 = m.run((15, 16), steps=80, warmup=20, scenarios=("persist", "iid_half"))
        for c1, c2 in zip(r1["cases"], r2["cases"]):
            self.assertEqual(c1["tape_sha256"], c2["tape_sha256"])
            for name in m.MODELS:
                self.assertAlmostEqual(c1["metrics"][name]["holdout_prequential_brier"],
                                       c2["metrics"][name]["holdout_prequential_brier"])
        with self.assertRaises(ValueError):
            m.tape("bad", 1, 50)
        with self.assertRaises(ValueError):
            m.run((1,), steps=20)


if __name__ == "__main__":
    unittest.main()
