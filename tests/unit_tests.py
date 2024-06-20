import unittest
import csv
from pyDeid import *
# from pyDeid.phi_types import *
# from pyDeid.process_note import *
# from pyDeid.wordlists import *
filepath = 'C:/Users/kairu/OneDrive/Desktop/Everything/Unity Health/new_pyDeid/pyDeid/tests/'
# pyDeid(original_file = 'C:/Users/kairu/OneDrive/Desktop/Everything/Unity Health/new_pyDeid/pyDeid/tests/test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id'
#       )

# @unittest.skip("Skipping default arguments test")
# class TestCorrectOutputDefaultCsv(unittest.TestCase):
#    pyDeid(original_file = filepath + 'test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id'
#       )
   
#    def test_first_name_index(self):
#       with open(filepath + 'test__PHI.csv', 'r') as csvfile:
#          csv_reader = csv.reader(csvfile)
#          next(csv_reader)
#          self.assertEqual(next(csv_reader)[3], 'Justin')
   
#    def test_last_name_index(self):
#       with open(filepath + 'test__PHI.csv', 'r') as csvfile:
#          csv_reader = csv.reader(csvfile)
#          next(csv_reader)
#          next(csv_reader)
#          self.assertEqual(next(csv_reader)[3], 'Bieber')

   # def test_first_and_last_name_type(self):

# @unittest.skip("Skipping MLL only argument test")
class TestCorrectOutputMllOnlyCsv(unittest.TestCase):
   pyDeid(original_file = filepath + 'test.csv', 
      note_varname = 'note_text', 
      encounter_id_varname = 'genc_id',
      # mll_find_replace = True,
      regex_find = False,
      regex_replace = False,
      mll_file = filepath + 'mll_test.csv'
      )
   
   # def test_first_name_index(self):
   #    with open(filepath + 'test__PHI.csv', 'r') as csvfile:
   #       csv_reader = csv.reader(csvfile)
   #       next(csv_reader)
   #       self.assertEqual(next(csv_reader)[3], 'Justin')
   
   # def test_last_name_index(self):
   #    with open(filepath + 'test__PHI.csv', 'r') as csvfile:
   #       csv_reader = csv.reader(csvfile)
   #       next(csv_reader)
   #       next(csv_reader)
   #       self.assertEqual(next(csv_reader)[3], 'Bieber')

if __name__ == '__main__':
   # with open('./pyDeid/tests/test__PHI.csv', 'r') as csvfile:
   #    csv_reader = csv.reader(csvfile)
   #    print(next(csv_reader)[1][4])
   unittest.main()