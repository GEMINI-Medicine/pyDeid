import re
from .utils import load_file, add_type, PHI
import os
from .. import wordlists


class ContactFinder:
    def __init__(self):
        self.phis = {}
        self.note = ""
        self._load_phi_types()

    def set_note(self, new_note: str) -> None:
        self.note = new_note

    def set_phis(self, new_phis) -> None:
        self.phis = new_phis

    def _load_phi_types(self):
        DATA_PATH = wordlists.__path__[0]
        self.canadian_area_codes = load_file(
            os.path.join(DATA_PATH, "canadian_area_code.txt")
        )
        self.phone_disqualifiers = [
            "HR",
            "Heart",
            "BP",
            "SVR",
            "STV",
            "VT",
            "Tidal Volumes",
            "Tidal Volume",
            "TV",
            "CKS",
        ]

    def _is_common_area_code(
        self, area_code
    ):
        return area_code in self.canadian_area_codes

    def _is_probably_phone(self):
        for i in self.phone_disqualifiers:
            if re.search(r"\b" + i + r"\b"):
                return False
        return True

    def _telephone_match(self, m):

        start = m.start()
        end = m.end()

        next_seg = self.note[end:]

        extension = re.search(
            r"^(\s*(x|ex|ext|extension)\.?\s*[\(]?[\d]+[\)]?)\b",
            next_seg,
            re.IGNORECASE,
        )

        if extension:
            end = end + extension.end()

        return PHI(start, end, self.note[start:end])

    def _email(self):
        for m in re.finditer(
            r"\b([\w\.]+\w ?@ ?\w+[\.\w+]((\.\w+)?){,3}\.\w{2,3})\b", self.note
        ):
            add_type(PHI(m.start(), m.end(), m.group()), "Email Address", self.phis)

    def _telephone(self):

        # ###-###-#### (potentially with arbitrary line breaks)
        # accept number with line breaks only if it starts with a valid area code
        for m in re.finditer(
            r"\(?(\d{3})\s*[\)\.\/\-\, ]*\s*\d\s*\d\s*\d\s*[ \-\.\/]*\s*\d\s*\d\s*\d\s*\d",
            self.note,
        ):  # prepend all regex w/ '\(?' outside of testing

            if re.search(
                r"\(?\d{3}\s*[\)\.\/\-\, ]*\s*\d{3}\s*[ \-\.\/]*\s*\d{4}", m.group()
            ):
                add_type(
                    self._telephone_match(m), "Telephone/Fax", self.phis
                )
            elif self._is_common_area_code(m.group(1)):
                add_type(
                    self._telephone_match(m), "Telephone/Fax", self.phis
                )

        # ###-###-###
        for m in re.finditer(
            r"\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{3}\b", self.note
        ):
            if self._is_common_area_code(m.group(1)):
                add_type(
                    self._telephone_match(m), "Telephone/Fax", self.phis
                )

        # this will always create multiple matches with pattern 1, its ok, double obscure it.
        # ###-###-#####
        for m in re.finditer(
            r"\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{5}\b", self.note
        ):
            if self._is_common_area_code(m.group(1)):
                add_type(
                    self._telephone_match(m), "Telephone/Fax", self.phis
                )

        # ###-####-###
        for m in re.finditer(
            r"\(?\d{3}?\s?[\)\.\/\-\=\, ]*\s?\d{4}\s?[ \-\.\/\=]*\s?\d{3}\b", self.note
        ):
            add_type(self._telephone_match(m), "Telephone/Fax", self.phis)

    def find(self) -> None:
        """
        Mutates PHI object to have PHI of contact type from the note

        Preconditions:
            -
        """
        self._email()
        self._telephone()
        return self.phis
