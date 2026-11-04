import json
import unittest
from pathlib import Path

from scripts.audit_ea_compatibility import summarize_observations
from src.portfolio_analysis import sha256_file

ROOT=Path(__file__).resolve().parents[1]


def observation(identity, sample, code):
    return {'id':identity,'hasSamplingPoint':{'samplingPointType':{'notation':'F6'}},
        'hasSample':{'id':sample,'sampleMaterialType':{'notation':'2AZZ'}},
        'observedProperty':{'notation':code,'prefLabel':code},'hasUnit':'mg/l',
        'hasResult':{'numericValue':None,'upperBound':1.,'lowerBound':None},
        'phenomenonTime':'2025-01-01T10:00:00'}


class EvidenceBreakthroughTests(unittest.TestCase):
    def test_same_time_different_sample_does_not_join(self):
        result=summarize_observations([observation('1','A','0085'),observation('2','B','0135')])
        self.assertEqual(result['same_sample_bod_and_suspended_solids'],0)
        self.assertEqual(result['censoring_counts']['upper_bound'],2)

    def test_same_sample_joins(self):
        result=summarize_observations([observation('1','A','0085'),observation('2','A','0135')])
        self.assertEqual(result['same_sample_bod_and_suspended_solids'],1)

    def test_duplicates_rejected(self):
        row=observation('1','A','0085')
        with self.assertRaisesRegex(ValueError,'Duplicate'):summarize_observations([row,row])

    def test_canals_rejected(self):
        row=observation('1','A','0085');row['hasSamplingPoint']['samplingPointType']['notation']='FJ'
        with self.assertRaisesRegex(ValueError,'Nonriver'):summarize_observations([row])

    def test_current_artifact_manifest(self):
        path=ROOT/'audits/evidence_breakthrough/CURRENT_BRANCH_MANIFEST.json'
        manifest=json.loads(path.read_text())
        for relative,expected in manifest['files'].items():
            self.assertEqual(sha256_file(ROOT/relative),expected,relative)

