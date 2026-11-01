import copy,json,pathlib,unittest
from engine import a_review,b_review,b_dependency_sql
P=pathlib.Path(__file__).parent
class BoundaryTests(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((P/'b_data.json').read_text());self.rules=json.loads((P/'rules.json').read_text());self.row=json.loads((P/'a_cases.json').read_text())[0]
 def test_rule_boundary(self):
  self.row.update(event_date='2026-07-01',selected_rule='v1')
  self.assertEqual(a_review(self.row,self.rules)['flags'],['missing_documents','rule_mismatch'])
 def test_no_applicable_rule(self):
  self.row['event_date']='2027-01-01';self.assertEqual(a_review(self.row,self.rules)['flags'],['no_rule'])
 def test_zero_is_known(self):
  d={'contracts':[dict(id='X',asset='D',right='service',start='2026-01-01',end='2027-01-01',limit=0)],'dependencies':[]}
  e=dict(kind='asset',target='D',at='2026-01-01',rights=['service'])
  r=b_review(d,e);self.assertEqual(r['known_limit'],0);self.assertTrue(r['complete']);self.assertEqual(r,b_dependency_sql(d,e))
 def test_end_excluded(self):
  e=dict(kind='asset',target='DC1',at='2026-06-01',rights=['service']);self.assertEqual(b_review(self.data,e)['ids'],['C01','C07'])
 def test_same_asset_different_contracts_preserved(self):
  e=dict(kind='asset',target='DC1',at='2026-11-01',rights=['capacity']);r=b_review(self.data,e)
  self.assertEqual(r['ids'],['C02','C05','C08']);self.assertEqual(r['known_limit'],1500);self.assertEqual(r['duplicates'],['C05'])
 def test_missing_is_not_zero(self):
  e=dict(kind='asset',target='DC2',at='2026-11-01',rights=['service']);r=b_review(self.data,e)
  self.assertEqual(r['missing_limit'],['C12']);self.assertFalse(r['complete'])
 def test_repeated_dependency_does_not_multiply(self):
  self.data['dependencies']*=2;e=dict(kind='dependency',target='gridA',at='2026-11-01',rights=['capacity'])
  self.assertEqual(b_review(self.data,e),b_dependency_sql(self.data,e))
 def test_no_payment_authorization(self):
  r=a_review(self.row,self.rules);self.assertTrue(r['review_required']);self.assertFalse(r['payment_authorized'])
if __name__=='__main__':unittest.main()
