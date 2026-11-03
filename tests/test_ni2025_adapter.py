import unittest
import pandas as pd
from scripts.validate_ni2025 import adapt,MAPPING


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
