# from ..phi_types.utils import phi_dict_to_list
from typing import *


class PHIHandler:

    """
    Responsible for managing the current the current note and associated PHIs. 

    Manages relationship between find, prune and replace operations for the current note
    """


    def __init__(self, regex_replace=True, mll_rows = {} ): # figure out args 
        self.note= ''
        self.phis = {}

        self.regex_replace = regex_replace
        self.mll_rows = mll_rows
        self.finder = self.pruner = self.replacer = None
    

    def set_note(self, new_note: str) -> None:
        self.note = new_note
        handlers = [self.finder, self.pruner, self.replacer ]

        for handler in handlers:
            if handler is not None:
                handler.set_note(new_note)

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis
        handlers = [self.finder, self.pruner, self.replacer]

        for handler in handlers:
            if handler is not None:
                handler.set_phis(new_phis)

    def set_finder(self, finder):
        self.finder = finder

    def set_pruner(self, pruner):
        self.pruner = pruner

    def set_replacer(self, replacer = None):
        self.replacer = replacer
    
    def handle_string(self,
        note: str,
        row_from_mll: str = None       
    ) -> Tuple[List[Dict[str, str]], str]:

        self.set_note(note)
        self.set_phis({})

        found_phi = self.finder.find_phi(row_from_mll)
        self.set_phis(found_phi)

        # self.set_phis(prune_phi(note, found_phi))
        pruned_phi = self.pruner.prune_phi()
        self.set_phis(pruned_phi)


        surrogates = []
        new_note = ''
      
      
        if self.regex_replace:
            surrogates, new_note = self.replacer.replace_phi()

        return surrogates, new_note
    
    def handle_csv_row(self,
        row: Dict[str, str], errors: List[str],
        encounter_id_varname: str = "genc_id",
        note_id_varname: str = None,
        note_varname: str = "note_text",
        ) -> Tuple[int, int, List[str]]:
    
        """ Handle the note - with find, prune, and replace"""
        note = row[note_varname]
        new_note = ''
        surrogates = []
        found_phis = []
        
        try:
            # Handle MLL logic
            row_from_mll = None
            
            if self.mll_rows:
                enc_id = row[encounter_id_varname]
                row_from_mll = self.mll_rows.get(enc_id)

            # Process PHI
            surrogates, new_note = self.handle_string(
                note, row_from_mll
            )

            # found_phis = phi_dict_to_list(new_note, self.phis)  # Assuming this function is still needed

        except Exception as e:
            print("out", e)
            surrogates = [{'phi_start': '', 'phi_end': '', 'phi': '', 'surrogate_start': '', 'surrogate_end': '', 'surrogate': '', 'types': '', }]
            new_note = self.note

            if note_id_varname is not None:
                errors.append((row[encounter_id_varname], row[note_id_varname]))
            elif encounter_id_varname is not None:
                errors.append(row[encounter_id_varname])

        return errors, surrogates, new_note, self.phis