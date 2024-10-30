import re
from .utils import add_type, PHI


class OHIPFinder:
    def __init__(self):
        self.phis = {}
        self.note = ""

    def set_note(self, new_note: str) -> None:
        self.note = new_note

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis

    def find(self):

        self._ohip()

        return self.phis

    def _ohip(self):
        for m in re.finditer(
            r"\b\d{4}[- \/]?\d{3}[- \/]?\d{3}[- \/]?([a-zA-Z]?[a-zA-Z]?)\b", self.note
        ):
            add_type(PHI(m.start(), m.end(), m.group()), "OHIP", self.phis)
