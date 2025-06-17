from dataclasses import dataclass, field
import re
from typing import List, Set
from .PHITypeFinder import PHI, PHITypeFinder, PHIDict
from .utils import (
    is_common,
    is_type,
    is_unambig_common,
    is_commonest,
    merge_phi_dicts,
)


class NamesPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting names.
    """

    @dataclass
    class Config:
        # unambiguous first names
        female_names_unambig: List[str] = field(default_factory=list)
        male_names_unambig: List[str] = field(default_factory=list)
        all_first_names: List[str] = field(default_factory=list)

        # unambiguous last names
        last_names_unambig: List[str] = field(default_factory=list)
        all_last_names: List[str] = field(default_factory=list)

        # doctor first and last names
        doctor_first_names: List[str] = field(default_factory=list)
        doctor_last_names: List[str] = field(default_factory=list)

        # ambiguous first names
        female_names_ambig: List[str] = field(default_factory=list)
        male_names_ambig: List[str] = field(default_factory=list)
        last_names_ambig: List[str] = field(default_factory=list)

        # popular first names (ambiguous)
        female_names_popular: List[str] = field(default_factory=list)
        male_names_popular: List[str] = field(default_factory=list)
        last_names_popular: List[str] = field(default_factory=list)

        # medical phrases
        medical_phrases: List[str] = field(default_factory=list)

        # custom names
        custom_dr_first_names: List[str] = field(default_factory=list)
        custom_dr_last_names: List[str] = field(default_factory=list)
        custom_patient_first_names: List[str] = field(default_factory=list)
        custom_patient_last_names: List[str] = field(default_factory=list)

        # prefixes
        prefixes_unambig: Set[str] = field(default_factory=set)
        last_name_prefixes: Set[str] = field(default_factory=set)

        # NER Model
        ner_model: any = None

        # name indicators
        name_indicators: List[str] = field(
            default_factory=lambda: [
                "problem",
                "problem:",
                "proxy",
                "fellow",
                "staff",
                "daughter",
                "daughters",
                "dtr",
                "son",
                "brother",
                "sister",
                "mother",
                "mom",
                "father",
                "dad",
                "wife",
                "husband",
                "neice",
                "nephew",
                "spouse",
                "partner",
                "cousin",
                "aunt",
                "uncle",
                "granddaughter",
                "grandson",
                "grandmother",
                "grandmom",
                "grandfather",
                "granddad",
                "relative",
                "friend",
                "neighbor",
                "visitor",
                "family member",
                "lawyer",
                "priest",
                "rabbi",
                "coworker",
                "co-worker",
                "boyfriend",
                "girlfriend",
                "name is",
                "named",
                "rrt",
                "significant other",
                "jr",
                "caregiver",
                "proxys",
                "friends",
                "sons",
                "brothers",
                "sisters",
                "sister-in-law",
                "brother-in-law",
                "mother-in-law",
                "father-in-law",
                "son-in-law",
                "daughter-in-law",
                "dtr-in-law",
                "surname will be",
                "name will be",
                "name at discharge will be",
                "name at discharge is",
            ]
        )
        eponym_indicators: List[str] = field(
            default_factory=lambda: [
                "disease",
                "cyst",
                "catheter",
                "syndrome",
                "tumour",
                "forceps",
                "boil",
                "method",
                "test",
                "sign",
                "abscess",
                "canal",
                "duct",
                "clamp",
                "effect",
                "law",
            ]
        )

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or self.Config()

        self.custom_names = []
        if self.config.custom_dr_first_names is not None:
            self.custom_names.append(({name.upper() for name in self.config.custom_dr_first_names}, "Custom Doctor First Name"))
        if self.config.custom_dr_last_names is not None:
            self.custom_names.append(({name.upper() for name in self.config.custom_dr_last_names}, "Custom Doctor Last Name"))
        if self.config.custom_patient_first_names is not None:
            self.custom_names.append(({name.upper() for name in self.config.custom_patient_first_names}, "Custom Patient First Name"))
        if self.config.custom_patient_last_names is not None:
            self.custom_names.append(({name.upper() for name in self.config.custom_patient_last_names}, "Custom Patient Last Name"))

        self.namesets = [
            (self.config.female_names_unambig, "Female First Name (un)"),
            (self.config.male_names_unambig, "Male First Name (un)"),
            (self.config.last_names_unambig, "Last Name (un)"),
            (self.config.doctor_last_names, "Doctor Last Name"),
            (self.config.female_names_ambig, "Female First Name (ambig)"),
            (self.config.male_names_ambig, "Male First Name (ambig)"),
            (self.config.last_names_ambig, "Last Name (ambig)"),
            (self.config.female_names_popular, "Female First Name (popular/ambig)"),
            (self.config.male_names_popular, "Male First Name (popular/ambig)"),
            (self.config.last_names_popular, "Last Name (popular/ambig)"),
            # TODO: add patients here
        ]

    def __is_medical_eponym(self, text: str) -> bool:
        return text is not None and text.lower() in self.config.eponym_indicators

    def __is_name_indicator(self, text: str) -> bool:
        return text is not None and text.lower() in self.config.name_indicators

    def __is_probably_name(self, key: PHI, phi: PHIDict) -> bool:
        if (
            not is_common(key.phi)
            or (is_type(key, "Name", True, phi) and is_type(key, "(un)", True, phi))
            or (
                is_type(key, "Name", True, phi)
                and (re.search(r"\b(([A-Z])([a-z]+))\b", key.phi) or re.search("\b(([A-Z]+))\b", key.phi))
                or is_type(key, "popular", True, phi)
            )
        ):
            return True
        else:
            return False

    def __is_probably_prefix(self, text: str) -> bool:
        return text.upper() in self.config.prefixes_unambig

    def __first_pass(self, text: str) -> PHIDict:
        phi = {}
        word_pattern = re.compile("\w+")

        for word in word_pattern.finditer(text):
            for names, tag in self.namesets:
                if word.group().upper() in names:
                    phi.setdefault(PHI(word.start(), word.end(), word.group()), []).append(tag)
            for names, tag in self.custom_names:
                if (
                    word.group().upper() in names
                    and len(word.group().upper()) > 1
                    and not is_common(word.group())
                    and not is_commonest(word.group())
                    and not is_unambig_common(word.group())
                ):  # reduces false positives for initials in custom names
                    phi.setdefault(PHI(word.start(), word.end(), word.group()), []).append(tag)

        for phrase in self.config.medical_phrases:
            for m in re.finditer(phrase, text, re.IGNORECASE):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("MedicalPhrase")

        for name in self.config.doctor_first_names:
            for m in re.finditer(name, text, re.IGNORECASE):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Doctor First Name")

        return phi

    def __combine_prefix_and_lastname(self, phi: PHIDict) -> PHIDict:
        updated_phi = dict(phi)
        items = list(sorted(phi.items()))
        i = 0

        while i < (len(items) - 1):
            first_word_key = items[i][0]
            second_word_key = items[i + 1][0]

            first_word_value = items[i][1][0]
            second_word_value = items[i + 1][1][0]
            i += 1

            if first_word_value == "Last Prefix" and second_word_value == "Last Name":
                prefix_end = first_word_key.end
                last_name_start = second_word_key.start

                if last_name_start < prefix_end + 3:  # don't catch last names that occur way after

                    prefix_start = first_word_key.start
                    last_name_end = second_word_key.end

                    combined_prefix_and_lastname = first_word_key.phi + second_word_key.phi

                    updated_phi.setdefault(PHI(prefix_start, last_name_end, combined_prefix_and_lastname), []).append("Last Name")

        return updated_phi

    def __follows_name_indicator(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}
        for indicator in self.config.name_indicators:
            for m in re.finditer(r"\b(" + indicator + r")(s)?( *)(\-|\,|\.|\()?(  *)([A-Za-z]+\b)\b", text, re.IGNORECASE):
                start = m.start(6)
                end = m.end(6)

                key = PHI(start, end, m.group(6))

                if self.__is_probably_name(key, phi):
                    found_phi.setdefault(key, []).append("Name (NI)")

                string_after = text[end:]

                for n in re.finditer(r"^\b(and )?( *)([A-Za-z]+)\b", string_after, re.IGNORECASE):
                    word_after = n.group(3)
                    key_after = PHI(end + n.start(3), end + n.end(3), word_after)

                    if not self.__is_medical_eponym(word_after) and (
                        not self.__is_name_indicator(word_after)
                        and (
                            not is_common(word_after)
                            or (
                                (is_type(key_after, "Name", True, phi) and is_type(key_after, "\(un\)", True, phi))
                                or (is_type(key_after, "Name", True, phi) and re.search(r"\b(([A-Z])([a-z]+))\b", word_after))
                                or (not is_commonest(word_after) and is_type(key_after, "Name", True, phi))
                                or is_type(key_after, "popular", True, phi)
                            )
                        )
                    ):
                        if not re.search(r"\b[\d]\b", string_after):
                            found_phi.setdefault(key_after, []).append("Name2 (NI)")

                    elif re.search(r"and", m.group(1)) and not self.__is_medical_eponym(word_after):
                        if not (is_common(word_after) or self.__is_name_indicator(word_after)):
                            found_phi.setdefault(key_after, []).append("Name2 (NI)")

        return found_phi

    def __lastname_comma_firstname(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}
        for m in re.finditer(r"\b([A-Za-z]+)( ?\, ?)([A-Za-z]+)\b", text, re.IGNORECASE):
            start_1 = m.start(1)
            end_1 = m.end(1)

            start_2 = m.start(3)
            end_2 = m.end(3)

            key_1 = PHI(start_1, end_1, m.group(1))
            key_2 = PHI(start_2, end_2, m.group(3))

            if is_type(key_2, "Name", True, phi) and is_type(key_1, "Name (ambig)", True, phi) and not self.__is_name_indicator(m.group(1)):
                found_phi.setdefault(key_1, []).append("Last Name (LF)")
                found_phi.setdefault(key_2, []).append("First Name2 (LF)")

            if is_type(key_2, "First Name", True, phi):

                if (is_type(key_1, "Last Name", True, phi) and not is_commonest(m.group(1)) and not self.__is_name_indicator(m.group(1))) or (
                    not is_common(m.group(1)) and not is_commonest(m.group(1))
                ):
                    found_phi.setdefault(key_1, []).append("Last Name (LF)")
                    found_phi.setdefault(key_2, []).append("First Name3 (LF)")

        return found_phi

    def __multiple_names_following_title(self, text: str, phi: PHIDict) -> PHIDict:
        plural_titles = ["doctors", "drs", "drs\.", "professors"]

        found_phi = {}
        for title in plural_titles:
            for m in re.finditer(r"\b(((" + title + r" +)([A-Za-z]+) *(and +)?\,? *)([A-Za-z]+) *(and +)?\,? *)([A-Za-z]+)?\b", text, re.IGNORECASE):
                keys = []

                name1 = m.group(4)
                keys.append(PHI(m.start(4), m.end(4), name1))

                name2 = m.group(6)
                if name2 is not None:
                    keys.append(PHI(m.start(6), m.end(6), name2))

                name3 = m.group(8)
                if name3 is not None:
                    keys.append(PHI(m.start(8), m.end(8), name3))

                for key in keys:
                    if (not is_commonest(key[2])) or is_type(key, "Name", True, phi):
                        found_phi.setdefault(key, []).append("Name5 (PTitle)")

        return found_phi

    def __followed_by_md(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for m in re.finditer(
            r"\b((([A-Za-z\']+|[A-Za-z]\.) +)?((\([A-Za-z\']+\)|[A-Za-z\']+|[A-Za-z]\.) +)?([A-Za-z\-\']+)((\, *)|(\s+))(rrt|md|m\.d\.|crt|np|rn|nnp|msw|r\.n\.|staff|fellow|resident|\(fellow\)|\(resident\)|\(staff\))(\.|\,)*)",
            text,
            re.IGNORECASE,
        ):

            if not re.search(r"(m\.?d\.?\')", text) and not re.search(r"(m\.?d\.?s)", text):

                first_name = m.group(3)

                if first_name is not None:
                    first_name_key = PHI(m.start(3), m.end(3), first_name)

                    if len(first_name) == 1 or (len(first_name) == 2 and re.search(r"\b([A-Za-z])\.+\b", first_name, re.IGNORECASE)):
                        found_phi.setdefault(first_name_key, []).append("Name Initial (MD)")
                    elif self.__is_probably_name(first_name_key, phi):
                        found_phi.setdefault(first_name_key, []).append("Name6 (MD)")

                last_name = m.group(6)

                if last_name is not None:
                    last_name_key = PHI(m.start(6), m.end(6), last_name)

                    if self.__is_probably_name(last_name_key, phi):
                        found_phi.setdefault(last_name_key, []).append("Name8 (MD)")

                initials = m.group(5)

                if initials is not None and last_name is not None:
                    initials_key = PHI(m.start(5), m.end(5), initials)

                    if (
                        len(initials) == 1
                        or (len(initials) == 2 and re.search(r"\b([A-Za-z])\.+\b", initials))
                        or self.__is_probably_prefix(initials)
                    ):
                        found_phi.setdefault(initials_key, []).append("Name Initial (MD)")

                    elif self.__is_probably_name(initials_key, phi):
                        found_phi.setdefault(initials_key, []).append("Name7 (MD)")

        return found_phi

    def __follows_pcp_name(self, text: str, phi: PHIDict) -> PHIDict:
        names_pre = ["PCP", "physician", "provider", "created by"]

        found_phi = {}
        for pre in names_pre:
            for m in re.finditer(
                r"\b((" + pre + r"( +name)?( +is)?\s\s*)([A-Za-z\-]+)((\s*\,*\s*)? *)([A-Za-z\-]+\.?)(((\s*\,*\s*)? *)([A-Za-z\-]+))?)\b",
                text,
                re.IGNORECASE,
            ):
                keys = []

                first_name = m.group(5)
                if first_name is not None:
                    keys.append(PHI(m.start(5), m.end(5), first_name))

                initials = m.group(8)
                if initials is not None:
                    keys.append(PHI(m.start(8), m.end(8), initials))

                last_name = m.group(12)
                if last_name is not None:
                    keys.append(PHI(m.start(12), m.end(12), last_name))

                for key in keys:
                    if len(key[2]) == 1 or re.search(r"\b([A-Za-z])\.\b", key[2]):
                        found_phi.setdefault(key, []).append("Name Initial (PRE)")
                    elif self.__is_probably_name(key, phi):
                        found_phi.setdefault(key, []).append("Name9 (PRE)")

            for m in re.finditer(
                r"\b(("
                + pre
                + r"( +name)?( +is)? ?([\#\:\-\=\.\,])+ *)([A-Za-z\-]+)((\s*\,*\s*)? *)([A-Za-z\-]+\.?)((\s*\,*\s*)? *)([A-Za-z\-]+)?)\b",
                text,
                re.IGNORECASE,
            ):

                first_name = m.group(6)
                if first_name is not None:
                    first_name_key = PHI(m.start(6), m.end(6), first_name)

                initials = m.group(9)
                if initials is not None:
                    initials_key = PHI(m.start(9), m.end(9), initials)

                last_name = m.group(12)
                if last_name is not None:
                    last_name_key = PHI(m.start(12), m.end(12), last_name)

                first_found = False
                if first_name is not None:
                    if len(first_name) == 1 or re.search(r"\b([A-Za-z])\.\b", first_name, re.IGNORECASE):
                        found_phi.setdefault(first_name_key, []).append("Name Initial (NameIs)")
                        first_found = True

                    elif self.__is_probably_name(first_name_key, phi):
                        found_phi.setdefault(first_name_key, []).append("Name10 (NameIs)")
                        first_found = True

                if first_found:
                    second_found = False

                    if initials is not None:
                        if len(initials) == 2 or re.search(r"\b([A-Za-z])\.\b", initials, re.IGNORECASE):
                            found_phi.setdefault(initials_key, []).append("Name Initial (NameIs)")
                            second_found = True

                        elif self.__is_probably_name(initials_key, phi):
                            found_phi.setdefault(initials_key, []).append("Name11 (NameIs)")
                            second_found = True

                        if second_found:
                            if last_name is not None:
                                if (len(last_name) == 1) or re.search(r"\b([A-Za-z])\.\b", last_name, re.IGNORECASE):
                                    found_phi.setdefault(last_name_key, []).append("Name Initial (NameIs)")

                                elif self.__is_probably_name(last_name_key, phi):
                                    found_phi.setdefault(last_name_key, []).append("Name12 (NameIs)")

        return found_phi

    def __prefixes(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}
        # Van Der Meer
        for pre in self.config.prefixes_unambig:
            for m in re.finditer(r"\b((" + pre + r")([\s\'\-])+ *)([A-Za-z]+)\b", text, re.IGNORECASE):
                prefix_key = PHI(m.start(2), m.end(2), m.group(2))

                last_name = m.group(4)
                last_name_key = PHI(m.start(4), m.end(4), last_name)

                if (not is_commonest(last_name)) or is_type(last_name_key, "Name", True, merge_phi_dicts(phi, found_phi, in_place=False)):
                    found_phi.setdefault(prefix_key, []).append("Name Prefix (Prefixes)")
                    found_phi.setdefault(last_name_key, []).append("Last Name (Prefixes)")

        return found_phi

    def __titles(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        specific_titles = ["MR", "MISTER", "MS"]

        # Mr. Sanders
        for title in specific_titles:
            for m in re.finditer(r"\b(" + title + r"\.( *))([A-Za-z\'\-]+)\b", text, re.IGNORECASE):
                potential_name = m.group(3)
                start = m.start(3)
                end = start + len(potential_name)
                key = PHI(start, end, potential_name)

                if is_type(key, "Name", True, phi):
                    phi.setdefault(key, []).append("Name13 (STitle)")
                elif not is_common(potential_name):
                    phi.setdefault(key, []).append("Name14 (STitle)")

        strict_titles = ["Dr", "DRS", "Mrs"]

        for title in strict_titles:
            for m in re.finditer(r"\b(" + title + r"\b\.? *)([A-Za-z\'\-]+)( ?)(\')?( ?)([A-Za-z]+)?( ?)([A-Za-z]+)?\b", text, re.IGNORECASE):

                word = m.group(2)

                start = m.start(2)
                end = m.end(2)
                key = PHI(start, end, word)

                if word.upper() in self.config.last_name_prefixes:
                    phi.setdefault(key, []).append("Last Name (STitle)")

                    next_word = m.group(6)
                    if next_word is not None:

                        if next_word.upper() in self.config.last_name_prefixes:
                            key = PHI(m.start(6), m.end(6), next_word)

                            phi.setdefault(key, []).append("Last Name (STitle)")

                            if m.group(8) is not None:
                                key = PHI(m.start(8), m.end(8), m.group(8))

                        else:
                            key = PHI(m.start(6), m.end(6), next_word)

                            if self.__is_probably_name(key, phi):
                                phi.setdefault(key, []).append("Last Name (STitle)")

                else:
                    starts_w_apostophe = re.search(r"\'([A-Za-z]+)", word)
                    ends_w_apostrophe = re.search(r"([A-Za-z]+)\'", word)

                    if starts_w_apostophe:
                        word = starts_w_apostophe.group(1)
                        start -= 1
                        key = PHI(start, end, word)

                    if ends_w_apostrophe:
                        word = ends_w_apostrophe.group(1)
                        key = PHI(start, end, word)

                phi.setdefault(key, []).append("Last Name (STitle)")

                # Dr. John
                if is_type(key, "First Name", True, phi):
                    phi.setdefault(key, []).append("First Name (STitle)")

                # Dr. John Smith
                if m.group(6) is not None:
                    potential_last_name = m.group(6)
                    potential_last_name_key = PHI(m.start(6), m.end(6), potential_last_name)

                    if (
                        self.__is_probably_name(potential_last_name_key, phi)
                        or (not is_commonest(potential_last_name))
                        or (is_type(potential_last_name_key, "Name", True, phi) and is_type(potential_last_name_key, "(un)", False, phi))
                        or (is_type(potential_last_name_key, "Name", True, phi) and re.search(r"\b(([A-Z])([a-z]+))\b", potential_last_name))
                    ):
                        phi.setdefault(potential_last_name_key, []).append("Name (STitle)")

        other_titles = [
            "MISTER",
            "DOCTOR",
            "DOCTORS",
            "MISS",
            "PROF",
            "PROFESSOR",
            "REV",
            "RABBI",
            "NURSE",
            "MD",
            "PRINCESS",
            "PRINCE",
            "DEACON",
            "DEACONESS",
            "CAREGIVER",
            "PRACTITIONER",
            "MR",
            "MS",
            "RESIDENT",
            "STAFF",
            "FELLOW",
        ]

        for title in other_titles:
            for m in re.finditer(r"\b(" + title + r"\b\.? ?)([A-Za-z]+) *([A-Za-z]+)?(\,)?\b", text, re.IGNORECASE):
                word = m.group(2)

                start = m.start(2)
                end = m.end(2)
                key = PHI(start, end, word)

                word_after = m.group(3)
                start_after = m.start(3)
                end_after = m.end(3)
                key_after = PHI(start_after, end_after, word_after)

                if word.upper in self.config.last_name_prefixes:
                    phi.setdefault(key, []).append("Last Name (Titles)")

                    next_word = m.group(8)
                    string_after = text[end:]

                    search_after = re.search(r"^( ?)(\')?( ?)([A-Za-z]+)\b", string_after)

                    if search_after:
                        token = search_after.group(4)
                        token_start = end + search_after.start(4)
                        token_end = end + search_after.end(4)

                        if token.upper in self.config.last_name_prefixes:
                            new_key = PHI(start, token_end, text[start:token_end])
                            phi.setdefault(new_key, []).append("Last Name (Titles)")

                            string_after_after = text[token_end:]

                            search_after_after = re.search(r"( ?" + token + "( ?))([A-Za-z]+)\b", string_after_after)

                            if search_after_after is not None:
                                word = search_after_after.group(3)
                                new_end = token_end + search_after_after.end(3)

                                key = PHI(token_end, new_end, text[start:new_end])
                        else:
                            new_key = PHI(token_start, token_end, token)

                            if self.__is_probably_name(new_key, phi) and len(token) > 1:
                                phi.setdefault(new_key, []).append("Last Name (Titles)")
                else:
                    apostrophes = re.search(r"(\')?([A-Za-z]+)(\')?", word)

                    if apostrophes.group(1) is not None:
                        word = apostrophes.group(1)
                        key = PHI(start + 1, end, word)

                    if apostrophes.group(1) is not None:
                        word = apostrophes.group(1)
                        key = PHI(start, end - 1, word)

                if word_after is not None:
                    if (not self.__is_medical_eponym(word_after)) and (
                        (not is_commonest(word_after))
                        or (is_type(key_after, "Name", True, phi) and is_type(key_after, "(un)", False, phi))
                        or (is_type(key_after, "Name", True, phi) and re.search(r"\b(([A-Z])([a-z]+))\b", word_after))
                    ):
                        phi.setdefault(key_after, []).append("Last Name (Titles)")
                        phi.setdefault(key, []).append("First Name (Titles)")
                elif key in phi:
                    if is_type(key, "Name", True, phi) and self.__is_probably_name(key, phi):
                        phi.setdefault(key, []).append("Last Name (Titles)")
                else:
                    if (word is not None) and (not is_common(word)) and self.__is_probably_name(key, phi):
                        phi.setdefault(key, []).append("Last Name (Titles)")
                    else:
                        phi.setdefault(key, []).append("Last Name (Titles ambig)")

        return found_phi

    def __follows_first_name(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for i in list(phi):  # transform to list because we are 1. iterating, 2. modifying
            if (is_type(i, "Male First Name", True, phi) or is_type(i, "Female First Name", True, phi)) and (
                is_type(i, "(un)", True, phi) or is_type(i, "pop", True, phi)
            ):
                string_after = text[i[1] :]

                no_middle_initial = re.search(r"^( +)([A-Za-z\']{2,})\b", string_after)

                if no_middle_initial:
                    key = PHI(i[1] + no_middle_initial.start(2), i[1] + no_middle_initial.end(2), no_middle_initial.group(2))

                    if key in phi:
                        if is_type(key, "Name", True, phi) and (self.__is_probably_name(key, phi)):
                            found_phi.setdefault(key, []).append("Last Name (NamePattern1)")
                            found_phi.setdefault(i, []).append("First Name4 (NamePattern1)")  # make it unambig

                    elif self.__is_probably_name(key, phi):
                        found_phi.setdefault(key, []).append("Last Name (NamePattern1)")
                        found_phi.setdefault(i, []).append("First Name5 (NamePattern1)")

                        middle_initial = re.search(r"^( +)([A-Za-z])(\.? )([A-Za-z\-][A-Za-z\-]+)\b", string_after)

                        if middle_initial:
                            initial_start = i[1] + middle_initial.start(2)
                            initial_key = PHI(initial_start, initial_start + 1, middle_initial.group(2))
                            last_name = middle_initial.group(4)
                            last_name_key = PHI(i[1] + middle_initial.start(4), i[1] + middle_initial.end(4), last_name)

                            if last_name_key in phi and not is_type(last_name_key, "Last Name", False, phi):
                                found_phi.setdefault(last_name_key, []).append("Last Name (NamePattern1)")
                                found_phi.setdefault(initial_key, []).append("Initial (NamePattern1)")
                                found_phi.setdefault(i, []).append("First Name11 (NamePattern1)")

                            else:
                                if re.search(r"( +)([A-Za-z])(\.? )([A-Za-z][A-Za-z]+)\b\s*", string_after):
                                    found_phi.setdefault(last_name_key, []).append("Last Name (NamePattern1)")
                                    found_phi.setdefault(initial_key, []).append("Initial (NamePattern1)")
                                    found_phi.setdefault(i, []).append("First Name6 (NamePattern1)")

                                elif not is_commonest(last_name):
                                    found_phi.setdefault(last_name_key, []).append("Last Name (NamePattern1)")
                                    found_phi.setdefault(initial_key, []).append("Initial (NamePattern1)")
                                    found_phi.setdefault(i, []).append("First Name7 (NamePattern1)")
        return found_phi

    def __precedes_last_name(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for i in list(phi):  # transform to list because we are 1. iterating, 2. modifying
            if is_type(i, "Last Name", True, phi) and is_type(i, "(un)", True, phi):
                string_before = text[: i[0]]

                first_name_exists = re.search(r"\b([A-Za-z]+)( *)$", string_before)

                if first_name_exists:
                    first_name = first_name_exists.group(1)
                    first_name_key = PHI(first_name_exists.start(1), first_name_exists.end(1), first_name)

                    if first_name_key in phi:
                        if is_type(first_name_key, "First Name", True, merge_phi_dicts(phi, found_phi, in_place=False)) and (
                            not self.__is_name_indicator(first_name)
                        ):
                            found_phi.setdefault(first_name_key, []).append("First Name8 (NamePattern2)")

                    elif not is_common(first_name):
                        found_phi.setdefault(first_name_key, []).append("First Name9 (NamePattern2)")

        return found_phi

    def __compound_last_names(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for i in list(phi):  # transform to list because we are 1. iterating, 2. modifying
            string_after = text[i[1] :]

            if is_type(i, "Last Name", False, phi):

                hyphenated_last_name = re.search(r"^-([A-Za-z]+)\b", string_after)

                if hyphenated_last_name:
                    found_phi.setdefault(
                        PHI(i[1] + hyphenated_last_name.start(1), i[1] + hyphenated_last_name.end(1), hyphenated_last_name.group(1)), []
                    ).append("Last Name (NamePattern3)")

                double_last_name = re.search(r"^( *)([A-Za-z]+)\b", string_after)

                if double_last_name:
                    last_name = double_last_name.group(2)
                    last_name_key = PHI(i[1] + double_last_name.start(2), i[1] + double_last_name.end(2), last_name)

                    if last_name_key in phi:
                        if not is_type(last_name_key, "ambig", True, phi) and not is_type(last_name_key, "Last Name", False, phi):
                            found_phi.setdefault(last_name_key, []).append("Last Name (NamePattern3)")

                    elif not is_common(last_name):
                        found_phi.setdefault(last_name_key, []).append("Last Name (NamePattern3)")

        return found_phi

    def __initials(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for i in list(phi):  # transform to list because we are 1. iterating, 2. modifying
            if (not is_type(i, "ambig", True, phi) or is_type(i, "(un)", True, phi)) and is_type(i, "Name", True, phi):
                string_before = text[: i[0]]

                two_initials = re.search(r"\b([A-Za-z][\. ] ?[A-Za-z]\.?) ?$", string_before)
                single_initial = re.search(r"\b([A-Za-z]\.?) ?$", string_before)

                if two_initials:
                    found_phi.setdefault(
                        PHI(i[0] - len(two_initials.group()), i[0] - len(two_initials.group()) + len(two_initials.group(1)), two_initials.group(1)),
                        [],
                    ).append("Initials (NamePattern4)")
                elif single_initial:
                    initial = single_initial.group(1)
                    initial_key = PHI(
                        i[0] - len(single_initial.group()), i[0] - len(single_initial.group()) + len(single_initial.group(1)), single_initial.group(1)
                    )

                    if len(initial) == 2 or len(initial) == 1:
                        found_phi.setdefault(initial_key, []).append("Initials (NamePattern4)")
                    if not is_type(i, "Last Name", 0, phi):
                        found_phi.setdefault(i, []).append("Last Name (NamePattern4)")

            if is_type(i, "Last Name", True, phi) and not is_type(i, "ambig", True, phi):
                string_before = text[: i[0]]

                two_initials = re.search(r"\b([A-Za-z][\. ] ?[A-Za-z]\.?) ?$", string_before)
                single_initial = re.search(r"\b([A-Za-z]\.?) ?$", string_before)

                if two_initials:
                    found_phi.setdefault(PHI(i[1] + two_initials.start(1), i[1] + two_initials.end(1), two_initials.group(1)), []).append(
                        "Initials (NamePattern5)"
                    )

                    if not is_type(i, "Last Name", False, phi):
                        found_phi.setdefault(i, []).append("Last Name (NamePattern5)")

                elif single_initial:
                    initial = single_initial.group(1)
                    initial_key = PHI(i[1] + single_initial.start(1), i[1] + single_initial.end(1), initial)

        return found_phi

    def __list_of_names(self, text: str, phi: PHIDict) -> PHIDict:
        found_phi = {}

        for i in list(phi):  # transform to list because we are 1. iterating, 2. modifying
            if is_type(i, "Last Name", False, phi) or is_type(i, "Male First Name", False, phi) or is_type(i, "Female First Name", False, phi):
                string_after = text[i[1] :]

                and_or = re.search(r"^ or|and ([A-Za-z]+)\b", string_after, re.IGNORECASE)
                and_or_symbols = re.search(r"^( ?[\&\+] ?)([A-Za-z]+)\b", string_after, re.IGNORECASE)
                three_names = re.search(r"^, ([A-Za-z]+)(,? and )([A-Za-z]+)\b", string_after, re.IGNORECASE)

                if and_or:
                    name = and_or.group(1)
                    name_key = PHI(i[1] + and_or.start(1), i[1] + and_or.end(1), name)

                    if is_type(name_key, "Name", True, phi) or is_common(name):
                        found_phi.setdefault(name_key, []).append("Last Name (NamePattern6)")

                elif and_or_symbols:
                    name = and_or_symbols.group(2)
                    name_key = PHI(i[1] + and_or_symbols.start(2), i[1] + and_or_symbols.end(2), name)

                    if not is_common(name):
                        found_phi.setdefault(name_key, []).append("Last Name (NamePattern6)")

                elif three_names:
                    name1 = three_names.group(1)
                    name2 = three_names.group(3)

                    name1_key = PHI(i[1] + three_names.start(1), i[1] + three_names.end(1), name1)
                    name2_key = PHI(i[1] + three_names.start(3), i[1] + three_names.end(3), name2)

                    if not is_common(name1):
                        found_phi.setdefault(name1_key, []).append("Last Name (NamePattern6)")
                    if not is_common(name2):
                        found_phi.setdefault(name2_key, []).append("Last Name (NamePattern6)")

        return found_phi

    def __ner(self, text: str, model):
        res = model(text)

        found_phi = {}

        for ent in res.ents:
            if ent.label_ == "PERSON":
                # check for firstname lastname
                m = re.search(r"(.*)\s(.*)", ent.text)
                if m is not None:
                    found_phi.setdefault(PHI(ent.start_char, ent.start_char + m.end(1), m.group(1)), []).append("First Name (NER)")
                    found_phi.setdefault(PHI(ent.start_char + m.start(2), ent.end_char, m.group(2)), []).append("Last Name (NER)")
                else:
                    found_phi.setdefault(PHI(ent.start_char, ent.end_char, ent.text), []).append("Name (NER)")

        return found_phi

    def find(self) -> PHIDict:
        phi = self.__first_pass(self.note)
        phi = self.__combine_prefix_and_lastname(phi)
        merge_phi_dicts(phi, self.__follows_name_indicator(self.note, phi))
        merge_phi_dicts(phi, self.__lastname_comma_firstname(self.note, phi))
        merge_phi_dicts(phi, self.__multiple_names_following_title(self.note, phi))
        merge_phi_dicts(phi, self.__followed_by_md(self.note, phi))
        merge_phi_dicts(phi, self.__follows_pcp_name(self.note, phi))
        merge_phi_dicts(phi, self.__prefixes(self.note, phi))
        merge_phi_dicts(phi, self.__titles(self.note, phi))
        merge_phi_dicts(phi, self.__follows_first_name(self.note, phi))
        merge_phi_dicts(phi, self.__precedes_last_name(self.note, phi))
        merge_phi_dicts(phi, self.__compound_last_names(self.note, phi))
        merge_phi_dicts(phi, self.__initials(self.note, phi))
        merge_phi_dicts(phi, self.__list_of_names(self.note, phi))
        if self.config.ner_model:
            merge_phi_dicts(phi, self.__ner(self.note, self.config.ner_model))

        return phi
