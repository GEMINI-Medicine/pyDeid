import re
from .PHITypeFinder import PHITypeFinder, PHI


class HospitalNamePHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting hospital names and their acronyms.
    """

    def __init__(self, hospitals: list[str], hospital_acronyms: list[str] = None):
        super().__init__()
        self.hospitals = hospitals
        self.hospital_acronyms = (
            hospital_acronyms if hospital_acronyms is not None else []
        )

    def find(self) -> list[PHI]:
        phi = {}

        for hospital in self.hospitals:
            terms = hospital.split(" ")
            n_terms = len(terms)

            if n_terms == 1:
                for m in re.finditer(hospital, self.note, re.IGNORECASE):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 2:
                for m in re.finditer(
                    r"\b(" + terms[0] + ")\s(" + terms[1] + r")\b", self.note, re.IGNORECASE
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

            if n_terms == 3:
                for m in re.finditer(
                    r"\b(" + terms[0] + ")\s(" + terms[1] + ")\s(" + terms[2] + r")\b",
                    self.note,
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
                    self.note,
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
                    self.note,
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
                    self.note,
                    re.IGNORECASE,
                ):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Hospital"
                    )

        for acronym in self.hospital_acronyms:
            for m in re.finditer(acronym, self.note):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                    "Site Acronym"
                )

        return phi