import re
from ..phi_types.utils import PHI, is_common, is_ambig, is_type, add_type
from typing import *


class PHIPruner:
    """A class representing all operations required to prune the PHIs for a given note"""

    def __init__(self):
        self.note = ''
        self.phis= {}

    def set_note(self,new_note:str)-> None:
        self.note = new_note

    def set_phis(self,new_phis) -> None:
        self.phis = new_phis
        
    def prune_phi(self)-> Dict[PHI, List[str]]:

        """
         Returns mutated PHI object containing a reduced set of PHIs after removing paradoxes and redundencies among the PHIs that exist from the note

        """

        phi_keys = sorted(self.phis.keys(), key=lambda x: x.start)
        self._check_ambiguous_types(phi_keys)
        self._remove_ambiguous_phi(phi_keys)
        phi_keys = sorted(self.phis.keys(), key=lambda x: x.start)  # Re-sort after removal
        self._remove_overlapping_phi(phi_keys)
        self._combine_overlapping_dates(phi_keys)

        return self.phis

    def _check_ambiguous_types(self, phi_keys: List[PHI]) -> None:

        """
        Checks for ambiguous types among the PHIs and adds probable types where necessary.

        This method analyzes adjacent PHIs to determine if they can be categorized as 'First Name' and 'Last Name'
        or if their ambiguity can be resolved.

        Preconditions:
            - phi_keys is sorted by their start positions
        """

        for i in range(len(phi_keys)):
            current_key = phi_keys[i]

            if i != 0:
                prev_key = phi_keys[i-1]

                if (
                    (is_type(prev_key, 'Name', 1, self.phis) and is_type(current_key, 'Name', 1, self.phis))
                    # and (not is_common(current_key.phi) or not is_common(prev_key.phi))
                    and not is_common(current_key.phi) and not is_common(prev_key.phi)
                    and not re.search(r'\.', prev_key.phi)
                    and not ((current_key.end - prev_key.start) < 3)
                ):
                    if (
                         (is_ambig(current_key, self.phis) and is_ambig(prev_key, self.phis) and is_type(prev_key, 'First Name', 1, self.phis) and is_type(current_key, 'Last Name', 1, self.phis)) or
                    (not is_ambig(current_key, self.phis) and is_ambig(prev_key, self.phis) and is_type(prev_key, 'First Name', 1, self.phis) and is_type(current_key, 'Last Name', 1, self.phis)) or
                    (is_ambig(current_key, self.phis) and not is_ambig(prev_key, self.phis) and is_type(prev_key, 'First Name', 1, self.phis) and is_type(current_key, 'Last Name', 1, self.phis))
                    ):
                        add_type(current_key, 'Last Name (probably)', self.phis)
                        add_type(prev_key, 'First Name (probably)', self.phis)

                    if (
                        (not is_ambig(current_key, self.phis) and is_ambig(prev_key, self.phis) and is_type(current_key, "First Name", 1, self.phis) and is_type(prev_key, "Last Name", 1, self.phis)) or
                    (is_ambig(current_key, self.phis) and not is_ambig(prev_key, self.phis) and is_type(current_key, "First Name", 1, self.phis) and is_type(prev_key, "Last Name", 1, self.phis))
                    ):
                        add_type(current_key, 'First Name (probably)', self.phis)
                        add_type(prev_key, 'Last Name (probably)', self.phis)

    def _remove_ambiguous_phi(self, phi_keys: List[PHI]) -> None:

        """
        Removes ambiguous PHI entries from the dictionary.

        This method identifies PHIs marked as ambiguous and deletes them from the dictionary.

        Preconditions:
            - phi_keys is sorted by PHI start positions.

        """

        for i in range(len(phi_keys)):
            current_key = phi_keys[i]
            if is_ambig(current_key, self.phis):
                del self.phis[current_key]

    def _remove_overlapping_phi(self, phi_keys: List[PHI]) -> None:

        """ 
        Identifies and removes overlapping PHI entries from the dictionary.
        
        Preconditions: 
            - phi_keys is sorted by PHI start positions

        """

        bad_keys = []
        for i in range(len(phi_keys)):
            current_key = phi_keys[i]
            if i != 0:
                previous_key = phi_keys[i-1]
                self._check_overlap_and_add_bad_keys(previous_key, current_key, bad_keys)

        for key in phi_keys:
            if any(re.search('MedicalPhrase', val) for val in self.phis[key]):
                bad_keys.append(key)

        # Remove PHI entries marked as bad
        for key in bad_keys:
            self.phis.pop(key, None)

    def _check_overlap_and_add_bad_keys(self, previous_key:PHI, current_key:PHI, bad_keys:List[PHI])-> None:

        """ 
        Checks for overlapping PHI entries and adds them to the list of 'bad' keys if necessary.

        This method evaluates the overlap between two PHI entries and determines whether they should be considered
        as redundant.

        """

        previous_start, previous_end = previous_key.start, previous_key.end
        current_start, current_end = current_key.start, current_key.end

        if current_start >= previous_start and current_end <= previous_end:
            bad_keys.append(current_key)

        elif current_start > previous_start and current_start < previous_end and current_end > previous_end:

            if self._should_remove_previous_key(previous_key, current_key):
                bad_keys.append(previous_key)
            else:
                self._combine_and_replace_keys(previous_key, current_key, bad_keys)

        elif current_start <= previous_start and current_end >= previous_end:
            bad_keys.append(previous_key)

        # if found PHI is part of a medical phrase, ignore it to reduce false positives
        elif any(re.search('MedicalPhrase', val) for val in self.phis[current_key]) and (current_start <= previous_start and current_end >= previous_end):
            bad_keys.extend([previous_key, current_key])

        elif any(re.search('MedicalPhrase', val) for val in self.phis[previous_key]) and (current_start > previous_start and current_start < previous_end and current_end > previous_end):
            bad_keys.extend([previous_key, current_key])

        # if any(re.search('MedicalPhrase', val) for val in phi[previous_key]):
        #     bad_keys.append(previous_key)

    def _should_remove_previous_key(self, previous_key:PHI, current_key:PHI)-> bool:

        """
        Determines if the previous PHI entry should be removed based on specific matching criteria with the current PHI entry. 
        
        Returns true if previous key should be removed, else false.

        """
        return any(re.match(r'^Day Month \[', x) for x in self.phis[previous_key]) and any(re.match(r'^Day Month Year \[', x) for x in self.phis[current_key]) or \
               any(re.match(r'^Month Day \[', x) for x in self.phis[previous_key]) and any(re.match(r'^Month Day Year \[', x) for x in self.phis[current_key])

    def _combine_and_replace_keys(self, previous_key:PHI, current_key:PHI, bad_keys:List[PHI])-> None:

        """
        Combines two overlapping PHI entries into a single entry and marks the original entries as bad.

        This method creates a new PHI entry that spans the range of both overlapping PHIs and merges their associated values.

        """
        new_key = PHI(previous_key.start, current_key.end, self.note[previous_key.start:current_key.end])
        new_val = self.phis[current_key] + self.phis[previous_key]
        bad_keys.extend([previous_key, current_key])
        self.phis[new_key] = new_val

    def _combine_overlapping_dates(self, phi_keys: List[PHI]):
        merged = True
        while merged:
            merged = False
            phi_keys = sorted(self.phis.keys(), key=lambda x: x.start)
            to_remove = set()
            to_add = []
            for i in range(len(phi_keys)):
                for j in range(i + 1, len(phi_keys)):
                    key1 = phi_keys[i]
                    key2 = phi_keys[j]
                    vals1 = self.phis.get(key1, [])
                    vals2 = self.phis.get(key2, [])
                    if any(re.search(r"(Date|Year|Month|Day|Time)", v, re.IGNORECASE) for v in vals1) and \
                    any(re.search(r"(Date|Year|Month|Day|Time)", v, re.IGNORECASE) for v in vals2):
                        if not (key1.end <= key2.start or key2.end <= key1.start):
                            new_start = min(key1.start, key2.start)
                            new_end = max(key1.end, key2.end)
                            new_key = PHI(new_start, new_end, self.note[new_start:new_end])
                            new_val = list(set(vals1 + vals2))
                            to_remove.update([key1, key2])
                            to_add.append((new_key, new_val))
                            merged = True
                            break
                if merged:
                    break
            for key in to_remove:
                self.phis.pop(key, None)
            for key, val in to_add:
                self.phis[key] = val
        return
