"""Metric tests with deterministic synthetic predictions, not experiment results."""

import unittest

import pandas as pd

from src.evaluate import evaluate_classification, evaluate_regression


class EvaluationTests(unittest.TestCase):
    def test_perfect_classification(self) -> None:
        metrics = evaluate_classification(
            pd.Series(["a", "b", "a"]), pd.Series(["a", "b", "a"])
        )
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["confusion_matrix"], [[2, 0], [0, 1]])

    def test_regression_metrics(self) -> None:
        metrics = evaluate_regression(pd.Series([1.0, 2.0]), pd.Series([1.0, 3.0]))
        self.assertAlmostEqual(metrics["mae"], 0.5)
        self.assertAlmostEqual(metrics["rmse"], 2**-0.5)


if __name__ == "__main__":
    unittest.main()

