import re
from .utils import is_unambig_common, add_type, PHI, load_file
import os
from .. import wordlists


class AddressFinder:
    def __init__(self ):
        self.phis = {}
        self.note = ''
      
        self._load_phi_types()

    def set_note(self,new_note:str)-> None:
        self.note = new_note
  
    def set_phis(self,new_phis) -> None:
        self.phis = new_phis
    
    def _load_locations(self, DATA_PATH):
        self.local_places_unambig = load_file(os.path.join(DATA_PATH, 'local_places_unambig_v2.txt'), optimization='iteration')
        self.apt_indicators = ["apt", "suite"] #only check these after the street address is found
        self.street_add_suff = ["park", "drive", "street", "road", "lane", "boulevard", "blvd", "avenue", "highway", "circle","ave", "place", "rd", "st"]
        # Strict street address suffix: case-sensitive match on the following, 
        #     and will be marked as PHI regardless of ambiguity (common words)
        self.strict_street_add_suff = ["Park", "Drive", "Street", "Road", "Lane", "Boulevard", "Blvd", "Avenue", "Highway","Ave", "Rd", "PARK", "DRIVE", "STREET", "ROAD", "LANE", "BOULEVARD", "BLVD", "AVENUE", "HIGHWAY","AVE", "RD"]

 
    def _load_phi_types(self):
        DATA_PATH = wordlists.__path__[0]

       
        self._load_locations(DATA_PATH)


    def _address(self):

        for place in self.local_places_unambig:
            
            for m in re.finditer(place, self.note, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Location (un)', self.phis)
        
        for suff in self.strict_street_add_suff:
            
            for m in re.finditer(r'\b(([0-9]+ +)?(([A-Za-z\.\']+) +)?([A-Za-z\.\']+) +\b' + suff + r'\.?\b)\b', self.note):
                start = m.start()
                end = m.end()
                
                next_seg = self.note[end:]
                
                for ind in self.apt_indicators:
                    
                    apt = re.search(r'^\b(' + ind + r'\.?\#? +[\w]+)\b', next_seg)

                    if apt:
                        end = end + apt.end()

                if m.group(3) is not None:
                    if is_unambig_common(m.group(5)):
                        add_type(PHI(start, end, self.note[start:end]), 'Street Address', self.phis)
                        
                elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                    add_type(PHI(start, end, self.note[start:end]), 'Street Address', self.phis)
                    
        for suff in self.street_add_suff:
            
            for m in re.finditer(r'\b(([0-9]+) +(([A-Za-z]+) +)?([A-Za-z]+) +' + suff + r')\b', self.note, re.IGNORECASE):
                
                if m.group(3) is not None and len(m.group(3)) == 0:
                    if is_unambig_common(m.group(5)):
                        add_type(PHI(m.start(), m.end(), m.group()), 'Street Address', self.phis)
                        
                elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Street Address', self.phis)

    def _postal_code(self):
        for m in re.finditer(r'\b([a-zA-Z]\d[a-zA-Z][ \-]?\d[a-zA-Z]\d)\b', self.note):
            add_type(PHI(m.start(), m.end(), m.group()), 'Postalcode', self.phis)
    
    

  
    def find(self):
        self._postal_code()
        self._address()


        return self.phis

