import unittest
import numpy as np
import pandas as pd
from scripts.run_scientific_sprint import bootstrap_weights, interval, sampling_null, station_stats


class ScientificSprintTests(unittest.TestCase):
    def test_null_retains_station_counts_and_is_deterministic(self):
        first, result = sampling_null([100,100,100],[30,0,0],draws=1000)
        second, _ = sampling_null([100,100,100],[30,0,0],draws=1000)
        np.testing.assert_equal(first, second)
        self.assertEqual(result['observed_hhi'], 1)
        self.assertLess(result['mc_upper_tail'], .01)

    def test_null_rejects_impossible_counts(self):
        with self.assertRaises(ValueError):
            sampling_null([2],[3])

    def test_bootstrap_resamples_whole_paired_stations(self):
        weights = bootstrap_weights(2,draws=100)
        np.testing.assert_equal(weights.sum(axis=1),2)
        frame=pd.DataFrame({'station_code':['A','A','B'],
            'actual_do_mg_l':[1.,6.,2.], 'predicted_do_mg_l':[3.,3.,5.],
            'predicted_low_do':[True,True,False]})
        stats=station_stats(frame)
        self.assertEqual(stats.loc['A','n'],2)
        self.assertEqual(stats.loc['A','fp'],1)
        self.assertEqual(stats.loc['B','fn'],1)
        self.assertEqual(stats.loc['A','ae'],5.)
        self.assertTrue(((weights @ stats.n.to_numpy())>=2).all())

    def test_intervals_report_undefined_replicates(self):
        result=interval([1.,2.,np.nan])
        self.assertEqual(result['undefined_replicates'],1)
        self.assertEqual(result['valid_replicates'],2)

