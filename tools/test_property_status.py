import unittest
from property_status import combined_status

class BuyerStatusTests(unittest.TestCase):
 def test_early_furnishing_needs_review(self):
  for stage in ('green','act14','act15'):
   for furniture in ('furnished','partial'):
    self.assertEqual(combined_status(stage,furniture),'review')
 def test_early_unstated_furniture_stays_early(self):
  self.assertEqual(combined_status('act14','unknown'),'act14')
 def test_no_stage_inference_from_furnishing(self):
  self.assertEqual(combined_status('unknown','furnished'),'furnished_stage_unknown')
 def test_act16_combined_statuses(self):
  for f in ('furnished','partial','unfurnished'):
   self.assertEqual(combined_status('act16',f),'act16_'+f)
 def test_unspecified_not_assumed_unfurnished(self):
  self.assertEqual(combined_status('act16','unknown'),'act16_unspecified')
 def test_conflict_not_ready(self):
  self.assertEqual(combined_status('act16','conflict'),'review')
  self.assertEqual(combined_status('conflict','furnished'),'review')
 def test_land(self):
  self.assertEqual(combined_status('not_applicable','unknown'),'not_applicable')

if __name__=='__main__':unittest.main()
