from typing import List, Tuple
import re
from .PHITypeFinder import PHIDict, PHITypeFinder, PHI


class PostalCodePHIType(PHITypeFinder):
    """
    PHIType implementation for detecting and handling postal codes.
    """

    def find(self, text: str) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b([a-zA-Z]\d[a-zA-Z][ \-]?\d[a-zA-Z]\d)\b", text):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Postalcode")

        return phi

    # def prune(self, text: str, start_index: int, end_index: int) -> str:
    #     pass

    # def replace(self, text: str, phi_list: list[PHI] = None) -> tuple[str, list[PHI]]:
    #     pass

    @property
    def name(self):
        return self._name


def generate_postal_code():
    letters = random.choices(string.ascii_uppercase, k=3)
    numbers = random.choices(string.digits, k=3)

    res = ""

    for i in range(3):
        res = res + letters[i] + numbers[i]

    return res
