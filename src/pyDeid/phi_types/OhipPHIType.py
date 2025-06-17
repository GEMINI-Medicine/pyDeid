from typing import Dict, List
import re
from .PHITypeFinder import PHITypeFinder, PHI, PHIDict


class OhipPHIType(PHITypeFinder):
    """
    Concrete implementation of PHIType for detecting OHIP numbers.
    """

    def find(self, text: str) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b\d{4}[- \/]?\d{3}[- \/]?\d{3}[- \/]?([a-zA-Z]?[a-zA-Z]?)\b", text):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("OHIP")

        return phi

    @property
    def name(self):
        return "OHIP"
