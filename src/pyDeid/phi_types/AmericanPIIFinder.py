import re
from .utils import add_type, PHI, load_file
import os
import wordlists


class AmericanPIIFinder:
    def __init__(self, types: list[str] = ["ssn", "zip"]):
        self.phis = {}
        self.note = ""
        self.types = types
        self._load_phi_types()

    def set_note(self, new_note: str) -> None:
        self.note = new_note

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis

    def _load_states(self, DATA_PATH):
        self.us_states = load_file(
            os.path.join(DATA_PATH, "us_states.txt"), optimization="iteration"
        )

    def _load_phi_types(self):
        DATA_PATH = wordlists.__path__[0]

        if "zip" in self.types:
            self._load_states(DATA_PATH)

    def _zip_code(self):
        for state in self.us_states:
            for m in re.finditer(
                r"\b" + state + " *[\.\,]*\.*\s*(\d{5}[-]?[0-9]*)\b",
                self.note,
                re.IGNORECASE,
            ):
                add_type(PHI(m.start(1), m.end(1), m.group(1)), "Zipcode", self.phis)

    def _ssn(self):
        for m in re.finditer(r"\b\d\d\d([- /]?)\d\d\1\d\d\d\d\b", self.note):
            add_type(PHI(m.start(), m.end(), m.group()), "SSN", self.phis)

    def find(self):
        if "zip" in self.types:
            self._zip_code()

        if "ssn" in self.types:
            self._ssn()

        return self.phis
