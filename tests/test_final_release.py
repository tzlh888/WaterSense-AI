import unittest
import pandas as pd
from scripts.prepare_final_release import sensitivity


class FinalReleaseTests(unittest.TestCase):
    def test_posthoc_omission_keeps_low_event_counts(self):
        data=pd.DataFrame({'actual_do_mg_l':[94.,2.,8.],
            'predicted_do_mg_l':[8.,5.,9.],'station_code':['A','B','C']})
        first,second=sensitivity(data)
        self.assertEqual(first['sample_count'],3)
        self.assertEqual(second['sample_count'],2)
        for key in ['true_positive_count','false_positive_count','false_negative_count','low_do_mae_mg_l']:
            self.assertEqual(first[key],second[key])
        self.assertEqual(first['true_negative_count']-second['true_negative_count'],1)

    def test_designated_posthoc_flag_must_be_unique(self):
        data=pd.DataFrame({'actual_do_mg_l':[94.,94.]})
        with self.assertRaisesRegex(ValueError,'exactly one'):sensitivity(data)
