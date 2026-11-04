import unittest
import pandas as pd
import json
import numpy as np
from pathlib import Path
from scripts.validate_ni2025 import adapt,MAPPING
from src.portfolio_analysis import sha256_file


def source_rows():
    rows=[]
    for station in [10014,10015]:
        row={'Station Code':station,'Date':'14/01/2025','Time':954,'Depth':0}
        for index,field in enumerate(MAPPING):
            row[f'Q.{index}']=''
            row[field]=8.
        rows.append(row)
    return rows


class NI2025AdapterTests(unittest.TestCase):
    def test_mapping_preserves_limits_and_historical_date_features(self):
        rows=source_rows();rows[0]['Q.1']=' <  '
        data,_,audit=adapt(pd.DataFrame(rows))
        self.assertEqual(data.loc[0,'bod_mg_l'],8)
        self.assertEqual(data.loc[0,'bod_is_below_limit'],1)
        self.assertEqual(data.loc[0,'station_code'],'UKGBNIF10014')
        self.assertEqual(data.loc[0,'sample_date'],'2025-01-14')
        self.assertEqual(audit['excluded_identity_conflict_rows'],0)

    def test_conflicting_identity_excludes_all_members(self):
        rows=source_rows();rows.append(dict(rows[0]));rows[-1]['BOD (mg/l)']=3.
        data,_,audit=adapt(pd.DataFrame(rows))
        self.assertEqual(audit['excluded_identity_conflict_rows'],2)
        self.assertEqual(list(data.station_code),['UKGBNIF10015'])

    def test_qualified_target_excluded(self):
        rows=source_rows();rows[0]['Q.3']='<'
        data,_,audit=adapt(pd.DataFrame(rows))
        self.assertEqual(len(data),1)
        self.assertEqual(audit['cleaning']['qualified_target_rows_excluded'],1)

    def test_pre2025_date_rejected(self):
        rows=source_rows();rows[0]['Date']='14/01/2024'
        with self.assertRaisesRegex(ValueError,'2025-only'):adapt(pd.DataFrame(rows))

    def test_saved_confirmation_identity_counts_and_freeze(self):
        root=Path(__file__).resolve().parents[1]
        out=root/'research_extension/ni2025_confirmation'
        freeze=json.loads((out/'FREEZE.json').read_text())
        self.assertEqual(sha256_file(root/'scripts/validate_ni2025.py'),freeze['adapter_sha256'])
        predictions=pd.read_csv(out/'predictions.csv.gz')
        cohort=pd.read_csv(out/'eligible_cohort.csv.gz')
        self.assertFalse(predictions.source_object_id.duplicated().any())
        np.testing.assert_array_equal(predictions.source_object_id,cohort.source_object_id)
        np.testing.assert_array_equal(predictions.actual_do_mg_l,cohort.dissolved_oxygen_mg_l)
        actual=predictions.actual_do_mg_l<4;detected=predictions.predicted_do_mg_l<4
        self.assertEqual(int((actual&detected).sum()),3)
        self.assertEqual(int((actual&~detected).sum()),17)
        reps=pd.read_csv(out/'bootstrap_replicates.csv.gz')
        self.assertEqual(int(reps.precision.isna().sum()),1844)
