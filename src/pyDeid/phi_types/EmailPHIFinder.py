import re
from .PHITypeFinder import PHI, PHITypeFinder, PHIDict


class EmailPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting email addresses.
    """

    def find(self) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b([\w\.]+\w ?@ ?\w+[\.\w+]((\.\w+)?){,3}\.\w{2,3})\b", self.note):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Email Address")

        return phi
