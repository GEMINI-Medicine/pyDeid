import re
from typing import List
from .PHITypeFinder import PHI, PHITypeFinder, PHIDict


class TelephoneFaxPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting telephone and fax numbers.
    """

    def __init__(self, area_codes: List[str] = None, disqualifiers: List[str] = None):
        super().__init__()
        self.area_codes = area_codes if area_codes is not None else []
        self.disqualifiers = disqualifiers if disqualifiers is not None else []

    def __is_common_area_code(self, x):
        return x in self.area_codes

    def __is_probably_phone(self, x):
        for i in self.phone_disqualifiers:
            if re.search(r"\b" + i + r"\b"):
                return False
        return True

    def __telephone_match(self, x, m):
        start = m.start()
        end = m.end()

        next_seg = x[end:]

        extension = re.search(r"^(\s*(x|ex|ext|extension)\.?\s*[\(]?[\d]+[\)]?)\b", next_seg, re.IGNORECASE)

        if extension:
            end = end + extension.end()

        return PHI(start, end, x[start:end])

    def find(self, text: str) -> PHIDict:
        phi = {}

        # ###-###-#### (potentially with arbitrary line breaks)
        # accept number with line breaks only if it starts with a valid area code
        for m in re.finditer(
            r"\(?(\d{3})\s*[\)\.\/\-\, ]*\s*\d\s*\d\s*\d\s*[ \-\.\/]*\s*\d\s*\d\s*\d\s*\d", text
        ):  # prepend all regex w/ '\(?' outside of testing

            if re.search(r"\(?\d{3}\s*[\)\.\/\-\, ]*\s*\d{3}\s*[ \-\.\/]*\s*\d{4}", m.group()):
                phi.setdefault(self.__telephone_match(text, m), []).append("Telephone/Fax")
            elif self.__is_common_area_code(m.group(1)):
                phi.setdefault(self.__telephone_match(text, m), []).append("Telephone/Fax")

        # ###-###-###
        for m in re.finditer(r"\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{3}\b", text):
            if self.__is_common_area_code(m.group(1)):
                phi.setdefault(self.__telephone_match(text, m), []).append("Telephone/Fax")

        # this will always create multiple matches with pattern 1, its ok, double obscure it.
        # ###-###-#####
        for m in re.finditer(r"\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{5}\b", text):
            if self.__is_common_area_code(m.group(1)):
                phi.setdefault(self.__telephone_match(text, m), []).append("Telephone/Fax")

        # ###-####-###
        for m in re.finditer(r"\(?\d{3}?\s?[\)\.\/\-\=\, ]*\s?\d{4}\s?[ \-\.\/\=]*\s?\d{3}\b", text):
            phi.setdefault(self.__telephone_match(text, m), []).append("Telephone/Fax")

        return phi

    @property
    def name(self):
        return "Telephone/Fax"
