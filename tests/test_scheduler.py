"""Run with python3 -m unittest discover -s tests -v."""
import unittest
from pathlib import Path
from src.scheduler import optimize_day
from src.data import load_case, MIX
from src.validation import run_validation

ROOT=Path(__file__).resolve().parents[1]

class SchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs,cls.days,cls.unassigned=load_case(ROOT/"data/raw/Input_JSON_Schedule_Optimization.json")

    def test_independent_exhaustive_examples(self):
        rows=run_validation()
        self.assertEqual(len(rows),6)
        self.assertTrue(all(r["result"]=="PASS" for r in rows))

    def test_first_day_notebook_regression(self):
        row=optimize_day(self.jobs,self.days[0],5)
        self.assertAlmostEqual(row["reference_cost_eur"],3.86126973,places=8)
        self.assertAlmostEqual(row["optimized_cost_eur"],3.79714186,places=8)

    def test_price_inputs_are_isolated(self):
        first=optimize_day(self.jobs,self.days[0],5)
        optimize_day(self.jobs,self.days[1],10)
        repeated=optimize_day(self.jobs,self.days[0],5)
        self.assertEqual(first,repeated)

    def test_constant_prices(self):
        row=optimize_day(self.jobs,[0.00005]*192,5)
        self.assertAlmostEqual(row["savings_eur"],0.0,places=10)

    def test_overloaded_machine(self):
        jobs=[{**j,"quantity":MIX[j["job_type_id"]]*6} for j in self.jobs]
        row=optimize_day(jobs,self.days[0],5)
        self.assertFalse(row["optimized_feasible"])
        self.assertIsNone(row["optimized_cost_eur"])

    def test_setup_boundary_and_data_quality(self):
        self.assertEqual([j["quantity"] for j in self.jobs],[10,15,4])
        self.assertEqual(self.unassigned,["Harden[1] TM2"])
        with self.assertRaises(AssertionError):optimize_day(self.jobs,self.days[0],7)

if __name__=="__main__":unittest.main()
