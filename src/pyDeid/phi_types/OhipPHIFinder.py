from typing import Dict, List
import re
from .PHITypeFinder import PHITypeFinder, PHI, PHIDict


class OhipPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting OHIP numbers.
    """

    def find(self) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b\d{4}[- \/]?\d{3}[- \/]?\d{3}[- \/]?([a-zA-Z]?[a-zA-Z]?)\b", self.note):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("OHIP")

        return phi
