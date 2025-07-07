from .PHITypeFinder import PHI, PHITypeFinder
from .utils import is_unambig_common
import re


class AddressPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting addresses.
    """

    apt_indicators = ["apt", "suite"]  # only check these after the street address is found
    street_add_suff = ["park", "drive", "street", "road", "lane", "boulevard", "blvd", "avenue", "highway", "circle", "ave", "place", "rd", "st"]
    # Strict street address suffix: case-sensitive match on the following,
    #     and will be marked as PHI regardless of ambiguity (common words)
    strict_street_add_suff = [
        "Park",
        "Drive",
        "Street",
        "Road",
        "Lane",
        "Boulevard",
        "Blvd",
        "Avenue",
        "Highway",
        "Ave",
        "Rd",
        "PARK",
        "DRIVE",
        "STREET",
        "ROAD",
        "LANE",
        "BOULEVARD",
        "BLVD",
        "AVENUE",
        "HIGHWAY",
        "AVE",
        "RD",
    ]

    def __init__(self, local_places_unambig: list[str] = None):
        super().__init__()
        if local_places_unambig is None:
            self.local_places_unambig = []
        else:
            self.local_places_unambig = local_places_unambig

    def find(self):
        phi = {}

        for place in self.local_places_unambig:
            for m in re.finditer(place, self.note, re.IGNORECASE):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Location (un)")

        for suff in self.strict_street_add_suff:
            for m in re.finditer(r"\b(([0-9]+ +)?(([A-Za-z\.\']+) +)?([A-Za-z\.\']+) +\b" + suff + r"\.?\b)\b", self.note):
                start = m.start()
                end = m.end()

                next_seg = self.note[end:]

                for ind in self.apt_indicators:

                    apt = re.search(r"^\b(" + ind + r"\.?\#? +[\w]+)\b", next_seg)

                    if apt:
                        end = end + apt.end()

                if m.group(3) is not None:
                    if is_unambig_common(m.group(5)):
                        phi.setdefault(PHI(start, end, self.note[start:end]), []).append("Street Address")

                elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                    phi.setdefault(PHI(start, end, self.note[start:end]), []).append("Street Address")

        for suff in self.street_add_suff:
            for m in re.finditer(r"\b(([0-9]+) +(([A-Za-z]+) +)?([A-Za-z]+) +" + suff + r")\b", self.note, re.IGNORECASE):

                if m.group(3) is not None and len(m.group(3)) == 0:
                    if is_unambig_common(m.group(5)):
                        phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Street Address")

                elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Street Address")

        return phi