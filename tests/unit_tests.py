import unittest
import csv
from pyDeid import *
import os

filepath = os.path.dirname(os.path.realpath(__file__))
# pyDeid(original_file = 'C:/Users/kairu/OneDrive/Desktop/Everything/Unity Health/new_pyDeid/pyDeid/tests/test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id'
#       )

# @unittest.skip("Skipping default arguments test")
class TestCorrectOutputDefaultCsv(unittest.TestCase):
   pyDeid(original_file = filepath + '\\test.csv', 
      note_varname = 'note_text', 
      encounter_id_varname = 'genc_id'
      )
   
   def setUp(self):
      print("Testing", self._testMethodName)
   
   def test_first_name_index(self):
      with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         self.assertEqual(next(csv_reader)[3], 'Justin')
   
   def test_last_name_index(self):
      with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         next(csv_reader)
         self.assertEqual(next(csv_reader)[3], 'Bieber')

   def test_correct_note_output(self):
      with open(filepath + '\\test__DE-IDENTIFIED.csv', 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         note = next(csv_reader)[2]
         with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)
            next(csv_reader)
            surrogate_name = next(csv_reader)[6]
         note_end_name = note.find(surrogate_name) + len(surrogate_name)
         self.assertNotEqual(note[:note_end_name], 'Justin Bieber')
         self.assertEqual(note[note_end_name:note_end_name+len(' was born on ')], ' was born on ')

# @unittest.skip("Skipping MLL only argument test")
# class TestCorrectOutputMllOnlyCsv(unittest.TestCase):
#    pyDeid(original_file = filepath + '\\test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id',
#       regex_find = False,
#       regex_replace = False,
#       mll_file = filepath + '\\mll_test.csv'
#       )

#    def setUp(self):
#       print("In method", self._testMethodName)

   # def test_first_name_index(self):
   #    with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
   #       csv_reader = csv.reader(csvfile)
   #       next(csv_reader)
   #       self.assertEqual(next(csv_reader)[3], 'Justin')
   
   # def test_last_name_index(self):
   #    with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
   #       csv_reader = csv.reader(csvfile)
   #       next(csv_reader)
   #       next(csv_reader)
   #       self.assertEqual(next(csv_reader)[3], 'Bieber')

if __name__ == '__main__':
   unittest.main()