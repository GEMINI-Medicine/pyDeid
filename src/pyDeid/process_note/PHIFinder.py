from typing import *
from ..phi_types.utils import CustomRegex

from ..phi_types import *

import pkg_resources


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

        # self.name_finder = NameFinder()
        # self.date_finder = DateFinder()
        # self.sin_finder = SINFinder()
        # self.ohip_finder = OHIPFinder()
        # self.mrn_finder = MRNFinder()
        # self.address_finder = AddressFinder()
        # self.hospital_finder = HospitalFinder()
        # self.contact_finder = ContactFinder()

        DATA_PATH = pkg_resources.resource_filename("pyDeid", "wordlists/")

        self.postal_code_finder = PostalCodePHIType()
        self.hospital_name_finder = HospitalNamePHIType(
            hospitals=load_file(os.path.join(DATA_PATH, "ontario_hospitals.txt"), optimization="iteration"),
            hospital_acronyms=load_file(os.path.join(DATA_PATH, "hospital_acronyms.txt"), optimization="iteration"),
        )
        self.address_finder = AddressPHIType(
            local_places_unambig=load_file(os.path.join(DATA_PATH, "local_places_unambig_v2.txt"), optimization="iteration"),
        )
        self.sin_finder = SinPHIType()
        self.ohip_finder = OhipPHIType()
        self.mrn_finder = MrnPHIType()
        self.telephone_fax_finder = TelephoneFaxPHIType(
            area_codes=load_file(os.path.join(DATA_PATH, "canadian_area_code.txt")),
            disqualifiers=[
                "HR",
                "Heart",
                "BP",
                "SVR",
                "STV",
                "VT",
                "Tidal Volumes",
                "Tidal Volume",
                "TV",
                "CKS",
            ],
        )
        self.email_finder = EmailPHIType()
        self.date_finder = DatesPHIType(
            invalid_time_pre_words=[
                "CPAP",
                "PS",
                "range",
                "bipap",
                "pap",
                "pad",
                "rate",
                "unload",
                "ventilation",
                "scale",
                "strength",
                "drop",
                "up",
                "cc",
                "rr",
                "cvp",
                "up",
                "in",
                "with",
                "ICP",
                "PSV",
                "of",
            ],
            invalid_time_post_words=[
                "packs",
                "psv",
                "puffs",
                "pts",
                "patients",
                "range",
                "scale",
                "mls",
                "liters",
                "litres",
                "drinks",
                "beers",
                "per",
                "esophagus",
                "tabs",
                "pts",
                "tablets",
                "systolic",
                "sem",
                "strength",
                "times",
                "bottles",
                "drop",
                "drops",
                "up",
                "cc",
                "mg",
                "/hr",
                "/hour",
                "mcg",
                "ug",
                "mm",
                "PEEP",
                "L",
                "dose",
                "doses",
                "cultures",
                "bpm",
                "ICP",
                "CPAP",
                "cm",
                "mm",
                "m",
                "sessions",
                "visits",
                "episodes",
                "drops",
                "breaths",
                "wbcs",
                "beat",
                "beats",
                "ns",  # ,'blood' creates many false negatives
            ],
        )
        self.names_finder = NamesPHIType(
            config=NamesPHIType.Config(
                female_names_unambig=load_file(os.path.join(DATA_PATH, "female_names_unambig_v2.txt")),
                male_names_unambig=load_file(os.path.join(DATA_PATH, "male_names_unambig_v2.txt")),
                all_first_names=load_file(os.path.join(DATA_PATH, "all_first_names.txt")),
                last_names_unambig=load_file(os.path.join(DATA_PATH, "last_names_unambig_v2.txt")),
                all_last_names=load_file(os.path.join(DATA_PATH, "all_last_names.txt")),
                doctor_first_names=load_file(os.path.join(DATA_PATH, "doctor_first_names.txt"), optimization="iteration"),
                doctor_last_names=load_file(os.path.join(DATA_PATH, "doctor_last_names.txt")),
                female_names_ambig=load_file(os.path.join(DATA_PATH, "female_names_ambig.txt")),
                male_names_ambig=load_file(os.path.join(DATA_PATH, "male_names_ambig.txt")),
                last_names_ambig=load_file(os.path.join(DATA_PATH, "last_names_ambig.txt")),
                female_names_popular=load_file(os.path.join(DATA_PATH, "female_names_popular_v2.txt")),
                male_names_popular=load_file(os.path.join(DATA_PATH, "male_names_popular_v2.txt")),
                last_names_popular=load_file(os.path.join(DATA_PATH, "last_names_popular_v2.txt")),
                prefixes_unambig=set(load_file(os.path.join(DATA_PATH, "prefixes_unambig.txt"))),
                last_name_prefixes=set(line.strip() for line in open(os.path.join(DATA_PATH, "last_name_prefixes.txt"))),
                medical_phrases=load_file(os.path.join(DATA_PATH, "medical_phrases.txt"), optimization="iteration"),
                ner_model=None,
            )
        )

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
            #     self.name_finder,
            #     self.date_finder,
            #     self.sin_finder,
            #     self.ohip_finder,
            #     self.mrn_finder,
            #     self.address_finder,
            #     self.hospital_finder,
            #     self.contact_finder,
        ]

        for finder in finders:
            if finder:
                finder.set_note(new_note)

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis
        finders = [
            # self.name_finder,
            # self.date_finder,
            # self.sin_finder,
            # self.ohip_finder,
            # self.mrn_finder,
            # self.address_finder,
            # self.hospital_finder,
            # self.contact_finder,
        ]

        for finder in finders:
            if finder:
                finder.set_phis(new_phis)

    def find_phi(self, row_from_mll=None) -> Dict[PHI, List[str]]:
        """
        Returns mutated PHI object containing PHIs of various types identified from the note

        """

        phi = self.phis

        if "names" in self.types:
            merge_phi_dicts(phi, self.names_finder.find(text=self.note))
            # if model:
            #     ner(x, phi, model)

        if "dates" in self.types:
            found_dates = self.date_finder.find(text=self.note)
            merge_phi_dicts(phi, found_dates)

        if "sin" in self.types:
            found_sins = self.sin_finder.find(text=self.note)
            merge_phi_dicts(phi, found_sins)

        if "ohip" in self.types:
            found_ohips = self.ohip_finder.find(text=self.note)
            merge_phi_dicts(phi, found_ohips)

        if "mrn" in self.types:
            found_mrns = self.mrn_finder.find(text=self.note)
            merge_phi_dicts(phi, found_mrns)

        if "locations" in self.types:
            found_post_codes = self.postal_code_finder.find(text=self.note)
            merge_phi_dicts(phi, found_post_codes)
            found_addresses = self.address_finder.find(text=self.note)
            merge_phi_dicts(phi, found_addresses)

        if "hospitals" in self.types:
            found_hospitals = self.hospital_name_finder.find(text=self.note)
            merge_phi_dicts(phi, found_hospitals)

        if "contact" in self.types:
            found_emails = self.email_finder.find(text=self.note)
            merge_phi_dicts(phi, found_emails)
            found_telephones = self.telephone_fax_finder.find(text=self.note)
            merge_phi_dicts(phi, found_telephones)

        # if "names" in self.types:

        #     phi = self.name_finder.name_first_pass()
        #     self.set_phis(phi)
        #     name_phi = self.name_finder.find()
        #     self.set_phis(name_phi)

        # if "dates" in self.types:
        #     date_phi = self.date_finder.find()
        #     self.set_phis(date_phi)

        # if "sin" in self.types:
        #     sin_phi = self.sin_finder.find()
        #     self.set_phis(sin_phi)

        # if "ohip" in self.types:
        #     ohip_phi = self.ohip_finder.find()
        #     self.set_phis(ohip_phi)

        # if "mrn" in self.types:
        #     mrn_phi = self.mrn_finder.find()
        #     self.set_phis(mrn_phi)

        # if "locations" in self.types:
        #     location_phi = self.address_finder.find()
        #     self.set_phis(location_phi)

        # if "hospitals" in self.types:
        #     hospital_phi = self.hospital_finder.find()
        #     self.set_phis(hospital_phi)

        # if "contact" in self.types:
        #     contact_phi = self.contact_finder.find()
        #     self.set_phis(contact_phi)

        self.set_phis(phi)

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
                for m in re.finditer(r"\b" + re.escape(val) + r"\b", self.note, re.IGNORECASE):
                    if m:
                        add_type(PHI(m.start(), m.end(), m.group()), column + " (MLL)", self.phis)
