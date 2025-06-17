import re
from .PHITypeFinder import PHITypeFinder, PHI


class HospitalNamePHIType(PHITypeFinder):
    """
    PHIType implementation for detecting and handling hospital names and their acronyms in text.
    This class searches for occurrences of hospital names (with support for up to six-word names)
    and hospital acronyms within a given text, returning their positions and matched values as PHI instances.
    """

    def __init__(self, hospitals: list[str], hospital_acronyms: list[str] = None):
        self.hospitals = hospitals
        self.hospital_acronyms = (
            hospital_acronyms if hospital_acronyms is not None else []
        )

    def find(self, text: str) -> list[PHI]:
        phi = {}

        for hospital in self.hospitals:
            terms = hospital.split(" ")
            n_terms = len(terms)

            if n_terms == 1:
                for m in re.finditer(hospital, text, re.IGNORECASE):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 2:
                for m in re.finditer(
                    r"\b(" + terms[0] + ")\s(" + terms[1] + r")\b", text, re.IGNORECASE
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 3:
                for m in re.finditer(
                    r"\b(" + terms[0] + ")\s(" + terms[1] + ")\s(" + terms[2] + r")\b",
                    text,
                    re.IGNORECASE,
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 4:
                for m in re.finditer(
                    r"\b("
                    + terms[0]
                    + ")\s("
                    + terms[1]
                    + ")\s("
                    + terms[2]
                    + ")\s("
                    + terms[3]
                    + r")\b",
                    text,
                    re.IGNORECASE,
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 5:
                for m in re.finditer(
                    r"\b("
                    + terms[0]
                    + ")\s("
                    + terms[1]
                    + ")\s("
                    + terms[2]
                    + ")\s("
                    + terms[3]
                    + ")\s("
                    + terms[4]
                    + r")\b",
                    text,
                    re.IGNORECASE,
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 6:
                for m in re.finditer(
                    r"\b("
                    + terms[0]
                    + ")\s("
                    + terms[1]
                    + ")\s("
                    + terms[2]
                    + ")\s("
                    + terms[3]
                    + ")\s("
                    + terms[4]
                    + ")\s("
                    + terms[5]
                    + r")\b",
                    text,
                    re.IGNORECASE,
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

        for acronym in self.hospital_acronyms:
            for m in re.finditer(acronym, text):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                    "Site Acronym"
                )

        return phi

    @property
    def name(self):
        pass
