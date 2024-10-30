from pyDeid.pyDeidBuilder import pyDeidBuilder
from pyDeid.CSVEvaluator import CSVEvaluator
import os

def test_fun_and_eval_functions():
    # Run FunFunc to create the file
   print(os.getcwd())

   deid = pyDeidBuilder() \
      .set_input_file(
         original_file = "./tests/test.csv",
         encounter_id_varname = "genc_id",
         note_varname = "note_text",
         note_id_varname = "note_id"
      )\
      .replace_phi() \
      .build()
   
   deid.run()

   evaluator = CSVEvaluator()
    
    # Run EvalFunc on the created file
   precision, recall, f1 = evaluator.add_ground_truth_file("./tests/ground_truth.csv", note_id_varname = "note_id")\
     .add_result_file("./tests/test__PHI.csv")\
     .evaluate()
    
    # Assert that all scores are 1
   assert precision == 1, f"Precision is {precision}, expected 1"
   assert recall == 1, f"Recall is {recall}, expected 1"
   assert f1 == 1, f"F1 score is {f1}, expected 1"
