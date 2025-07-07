from typing import List, Tuple
import re
from .PHITypeFinder import PHIDict, PHITypeFinder, PHI


class PostalCodePHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting postal codes.
    """

    def find(self) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b([a-zA-Z]\d[a-zA-Z][ \-]?\d[a-zA-Z]\d)\b", self.note):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Postalcode")

        return phi
