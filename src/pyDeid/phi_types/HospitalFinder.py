import re
from .utils import add_type, PHI, load_file
import os
from .. import wordlists


class HospitalFinder:
    def __init__(self):
        self.phis = {}
        self.note = ''
       
        self._load_phi_types()

    def set_note(self,new_note:str)-> None:
        self.note = new_note
  
    def set_phis(self,new_phis) -> None:
        self.phis = new_phis
    
    
    def _load_hospitals(self,DATA_PATH):
        self.hospitals = load_file(os.path.join(DATA_PATH, 'ontario_hospitals.txt'), optimization='iteration')
        self.hospital_acronyms = load_file(os.path.join(DATA_PATH, 'hospital_acronyms.txt'), optimization='iteration')

    def _load_phi_types(self):
        DATA_PATH = wordlists.__path__[0]
        
        self._load_hospitals(DATA_PATH)
  
    def _hospital(self):
        
        for hospital in self.hospitals:
            
            terms = hospital.split(" ")
            n_terms = len(terms)

            if n_terms == 1:
                for m in re.finditer(hospital, self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

            if n_terms == 2:
                for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + r')\b', self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

            if n_terms == 3:
                for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + r')\b', self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

            if n_terms == 4:
                for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + r')\b', self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

            if n_terms == 5:
                for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + ')\s(' + terms[4] + r')\b', self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

            if n_terms == 6:
                for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + ')\s(' + terms[4] + ')\s(' + terms[5] + r')\b', self.note, re.IGNORECASE):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', self.phis)

        for acronym in self.hospital_acronyms:
            for m in re.finditer(acronym, self.note):
                add_type(PHI(m.start(), m.end(), m.group()), 'Site Acronym', self.phis)
    
    def find(self):
    
        self._hospital()

        return self.phis

