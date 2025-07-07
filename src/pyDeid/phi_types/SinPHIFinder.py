from typing import Dict, List
import re
from .PHITypeFinder import PHITypeFinder, PHI, PHIDict


class SinPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting Canadian Social Insurance Numbers (SIN).
    """

    def find(self) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b(\d{3}([- \/]?)\d{3}\2\d{3})\b", self.note):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("SIN")

        return phi
