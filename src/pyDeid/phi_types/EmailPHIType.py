import re
from .PHITypeFinder import PHI, PHITypeFinder, PHIDict


class EmailPHIType(PHITypeFinder):
    """
    PHIType implementation for detecting and handling email addresses.
    """

    def find(self, text: str) -> PHIDict:
        phi = {}

        for m in re.finditer(r"\b([\w\.]+\w ?@ ?\w+[\.\w+]((\.\w+)?){,3}\.\w{2,3})\b", text):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Email Address")

        return phi

    @property
    def name(self):
        return "Email Address"
