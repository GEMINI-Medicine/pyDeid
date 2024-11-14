
from typing import *
from ..phi_types.utils import CustomRegex

from ..phi_types.NameFinder import *
from ..phi_types.DateFinder import *
from ..phi_types.ContactFinder import *
from ..phi_types.HospitalFinder import *
from ..phi_types.AddressFinder import *
from ..phi_types.MRNFinder import *
from ..phi_types.SINFinder import *
from ..phi_types.OHIPFinder import *
import ipdb

class PHIFinder:
    """A class representing all operations to find PHI values in a given note.

    Args:
        - custom_regexes: These are named arguments that will be taken as regexes to be scrubbed from the given note.
            The keyword/argument name itself will be used to label the PHI in the `phi_output`. Note that all custom patterns will be replaced with `<PHI>`.

        - model: The model loaded if named entity recognition (NER) is used

        - types: Various PHIs we want to identify
    """

    def __init__(
        self,
    ) -> None:
        """Initializes a PHIFinder object used to find PHIs on a note"""

        self.types = [
            "names",
            "dates",
            "sin",
            "ohip",
            "mrn",
            "locations",
            "hospitals",
            "contact",
        ]
        self.custom_regexes = []

        self.phis = {}
        self.note = ""

        self.name_finder = NameFinder()
        self.date_finder = DateFinder()
        self.sin_finder = SINFinder()
        self.ohip_finder = OHIPFinder()
        self.mrn_finder = MRNFinder()
        self.address_finder = AddressFinder()
        self.hospital_finder = HospitalFinder()
        self.contact_finder = ContactFinder()

    def set_types(
        self,
        types: List[str] = [
            "names",
            "dates",
            "sin",
            "ohip",
            "mrn",
            "locations",
            "hospitals",
            "contact",
        ],
    ):
        self.types = types

    def set_note(self, new_note: str) -> None:
        self.note = new_note
        finders = [
            self.name_finder,
            self.date_finder,
            self.sin_finder,
            self.ohip_finder,
            self.mrn_finder,
            self.address_finder,
            self.hospital_finder,
            self.contact_finder,
        ]

        for finder in finders:
            if finder:
                finder.set_note(new_note)

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis
        finders = [
            self.name_finder,
            self.date_finder,
            self.sin_finder,
            self.ohip_finder,
            self.mrn_finder,
            self.address_finder,
            self.hospital_finder,
            self.contact_finder,
        ]

        for finder in finders:
            if finder:
                finder.set_phis(new_phis)

    def find_phi(self, row_from_mll=None) -> Dict[PHI, List[str]]:

        """
        Returns mutated PHI object containing PHIs of various types identified from the note
        
        """
        

        if "names" in self.types:
           
            phi = self.name_finder.name_first_pass()
            self.set_phis(phi)
            name_phi = self.name_finder.find()
            self.set_phis(name_phi)

        if "dates" in self.types:
            date_phi = self.date_finder.find()
            self.set_phis(date_phi)

        if "sin" in self.types:
            sin_phi = self.sin_finder.find()
            self.set_phis(sin_phi)

        if "ohip" in self.types:
            ohip_phi = self.ohip_finder.find()
            self.set_phis(ohip_phi)

        if "mrn" in self.types:
            mrn_phi = self.mrn_finder.find()
            self.set_phis(mrn_phi)

        if "locations" in self.types:
            location_phi = self.address_finder.find()
            self.set_phis(location_phi)

        if "hospitals" in self.types:
            hospital_phi = self.hospital_finder.find()
            self.set_phis(hospital_phi)

        if "contact" in self.types:
            contact_phi = self.contact_finder.find()
            self.set_phis(contact_phi)

        if row_from_mll is not None:
            self._mll_process(row_from_mll)

        self._find_custom_regexes()

        return self.phis

    def _find_custom_regexes(self) -> None:
        """Mutates PHI object to have PHI satisfying the custom regexes from the note"""

        for custom_regex in self.custom_regexes:
            for m in re.finditer(r"" + custom_regex.pattern, self.note):
                start = m.start()
                end = m.end()
                key = PHI(start, end, m.group())

                add_type(key, custom_regex.phi_type, self.phis)

    def _mll_process(self, row_from_mll):
        for column in row_from_mll:
            val = row_from_mll[column]
            if val:
                for m in re.finditer(r'\b' + re.escape(val) + r'\b',self.note, re.IGNORECASE):
                    if m:
                        add_type(PHI(m.start(), m.end(), m.group()), column + " (MLL)", self.phis)
