import unittest, time
import csv
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from pyDeid.pyDeid import pyDeid

filepath = os.path.dirname(os.path.realpath(__file__))
# pyDeid(original_file = 'C:/Users/kairu/OneDrive/Desktop/Everything/Unity Health/new_pyDeid/pyDeid/tests/test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id'
#       )

# @unittest.skip("Skipping default arguments test")
class TestCorrectOutputDefaultCsv(unittest.TestCase):
   # start_time = time.time()

   pyDeid(
      original_file = os.path.join(filepath, 'test.csv'), 
      note_varname = 'note_text', 
      encounter_id_varname = 'genc_id'
      )
   
   # pyDeid(original_file = filepath + '\\tests_advanced\\100_words.csv', 
   #    note_varname = 'note_text', 
   #    encounter_id_varname = 'genc_id',
   #    )
   
   # end_time = time.time()
   
   # print("Elapsed runtime: " + end_time-start_time)
   def setUp(self):
      print("Testing", self._testMethodName)
   
   def test_first_name_index(self):
      with open(os.path.join(filepath, 'test__PHI.csv'), 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         self.assertEqual(next(csv_reader)[4], 'Justin')
   
   def test_last_name_index(self):
      with open(os.path.join(filepath, 'test__PHI.csv'), 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         next(csv_reader)
         self.assertEqual(next(csv_reader)[4], 'Bieber')

   def test_correct_note_output(self):
      with open(os.path.join(filepath, 'test__DE-IDENTIFIED.csv'), 'r') as csvfile:
         csv_reader = csv.reader(csvfile)
         next(csv_reader)
         note = next(csv_reader)[2]
         with open(os.path.join(filepath, 'test__PHI.csv'), 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)
            next(csv_reader)
            surrogate_name = next(csv_reader)[7]
         note_end_name = note.find(surrogate_name) + len(surrogate_name)
         self.assertNotEqual(note[:note_end_name], 'Justin Bieber')
         self.assertEqual(note[note_end_name:note_end_name+len(' was born on ')], ' was born on ')

# @unittest.skip("Skipping MLL only argument test")
# class TestCorrectOutputMllOnlyCsv(unittest.TestCase):
#    # pyDeid(original_file = filepath + '\\test.csv', 
#    #    note_varname = 'note_text', 
#    #    encounter_id_varname = 'genc_id',
#    #    regex_find = False,
#    #    regex_replace = False,
#    #    mll_file = filepath + '\\mll_test.csv'
#    #    )
   
#    pyDeid(original_file = filepath + '\\tests_advanced\\100_words.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id',
#       )
   
   # end_time = time.time()
   
   # print("Elapsed runtime: " + end_time-start_time)
#    def setUp(self):
#       print("Testing", self._testMethodName)
   
#    def test_first_name_index(self):
#       with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
#          csv_reader = csv.reader(csvfile)
#          next(csv_reader)
#          self.assertEqual(next(csv_reader)[3], 'Justin')
   
#    def test_last_name_index(self):
#       with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
#          csv_reader = csv.reader(csvfile)
#          next(csv_reader)
#          next(csv_reader)
#          self.assertEqual(next(csv_reader)[3], 'Bieber')

#    def test_correct_note_output(self):
#       with open(filepath + '\\test__DE-IDENTIFIED.csv', 'r') as csvfile:
#          csv_reader = csv.reader(csvfile)
#          next(csv_reader)
#          note = next(csv_reader)[2]
#          with open(filepath + '\\test__PHI.csv', 'r') as csvfile:
#             csv_reader = csv.reader(csvfile)
#             next(csv_reader)
#             next(csv_reader)
#             surrogate_name = next(csv_reader)[6]
#          note_end_name = note.find(surrogate_name) + len(surrogate_name)
#          self.assertNotEqual(note[:note_end_name], 'Justin Bieber')
#          self.assertEqual(note[note_end_name:note_end_name+len(' was born on ')], ' was born on ')

# @unittest.skip("Skipping MLL only argument test")
# class TestCorrectOutputMllOnlyCsv(unittest.TestCase):
   # pyDeid(original_file = filepath + '\\test.csv', 
   #    note_varname = 'note_text', 
   #    encounter_id_varname = 'genc_id',
   #    regex_find = False,
   #    regex_replace = False,
   #    mll_file = filepath + '\\mll_test.csv'
   #    )
   
   # pyDeid(original_file = filepath + '\\tests_advanced\\100_words.csv', 
   #    note_varname = 'note_text', 
   #    encounter_id_varname = 'genc_id',
   #    regex_find = False,
   #    regex_replace = False,
   #    mll_file = filepath + '\\tests_advanced\\mll_100_test.csv'
   #    )


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

# class TestCorrectOutputMllAndFindCsv(unittest.TestCase):
#    pyDeid(original_file = filepath + '\\test.csv', 
#       note_varname = 'note_text', 
#       encounter_id_varname = 'genc_id',
#       regex_replace = False,
#       mll_file = filepath + '\\mll_test.csv'
#       )

#    def setUp(self):
#       print("In method", self._testMethodName)

if __name__ == '__main__':
   unittest.main()
   