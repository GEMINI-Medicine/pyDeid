import re
from .utils import add_type, PHI

class SINFinder:
    def __init__(self):
        self.phis = {}
        self.note = ''
         

    def set_note(self,new_note:str)-> None:
        self.note = new_note
  
    def set_phis(self,new_phis) -> None:
        self.phis = new_phis
    
    def find(self):
       
        self._sin()
     
        return self.phis

    def _sin(self):
        for m in re.finditer(r'\b(\d{3}([- \/]?)\d{3}\2\d{3})\b', self.note):
            add_type(PHI(m.start(), m.end(), m.group()), 'SIN', self.phis)

  