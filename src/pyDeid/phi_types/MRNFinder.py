import re
from .utils import add_type, PHI


class MRNFinder:
    def __init__(self):
        self.phis = {}
        self.note = ""

    def set_note(self, new_note: str) -> None:
        self.note = new_note

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis

    def find(self):

        self._mrn()

        return self.phis

    def _mrn(self):
        for m in re.finditer(
            r"((mrn|medical record|hospital number)( *)(number|num|no|#)?( *)[\)\#\:\-\=\s\.]?( *)(\t*)( *)[a-zA-Z]*?((\d+)[\/\-\:]?(\d+)?))[a-zA-Z]*?",
            self.note,
            re.IGNORECASE,
        ):
            add_type(PHI(m.start(9), m.end(9), m.group(9)), "MRN", self.phis)
