import os
import re
from collections import namedtuple
from .. import wordlists


DATA_PATH = wordlists.__path__[0]


PHI = namedtuple("PHI", ["start", "end", "phi"])


CustomRegex = namedtuple("CustomRegex", ["phi_type", "pattern", "surrogate_builder_fn", "arguments"])


name_indicators = ["problem","problem:", "proxy", "fellow", "staff", "daughter","daughters", "dtr", "son", "brother","sister", "mother", "mom", "father", "dad", "wife", "husband", "neice", "nephew", "spouse", "partner", "cousin", "aunt", "uncle", "granddaughter", "grandson", "grandmother", "grandmom", "grandfather", "granddad", "relative", "friend", "neighbor", "visitor", "family member", "lawyer", "priest", "rabbi", "coworker", "co-worker", "boyfriend", "girlfriend", "name is", "named", "rrt", "significant other", "jr", "caregiver", "proxys", "friends", "sons", "brothers", "sisters", "sister-in-law", "brother-in-law", "mother-in-law", "father-in-law", "son-in-law", "daughter-in-law", "dtr-in-law", "surname will be", "name will be", "name at discharge will be", "name at discharge is"]
eponym_indicators = ["disease", "cyst", "catheter", "syndrome", "tumour", "forceps", "boil", "method", "test", "sign", "abscess", "canal", "duct", "clamp", "effect", "law"]

def create_custom_regex(phi_type, pattern, surrogate_builder_fn, arguments=[]):
    # Create a CustomRegex instance, using an empty list as the default for arguments
    return CustomRegex(phi_type, pattern, surrogate_builder_fn, arguments)

def load_file(filename, optimization="lookup"):
    if optimization == "lookup":
        return {line.strip().upper() for line in open(filename)}
    elif optimization == "iteration":
        return [line.strip().upper() for line in open(filename)]


unambig_common_words = load_file(os.path.join(DATA_PATH, "notes_common.txt"))


medical_words = load_file(os.path.join(DATA_PATH, "sno_edited.txt"))
very_common_words = load_file(os.path.join(DATA_PATH, "commonest_words.txt"))
just_common_words = load_file(os.path.join(DATA_PATH, "common_words.txt"))


common_words = medical_words | very_common_words | just_common_words


def is_type(key: str, phitype: str, pattern: bool, phi):
    types = phi.get(key)
    if types is not None:
        for val in phi.get(key):
            if pattern:
                if re.search(phitype, val):
                    return True
            else:
                return val == phitype


def is_ambig(key, phi):
    types = phi.get(key)

    if all(re.search("ambig", val) for val in types):
        return True
    else:
        return False


def add_type(key, phitype, phi):
    phi.setdefault(key, []).append(phitype)

def add_phi_list(phi_list, phitype, phi):
    for key in phi_list:
        add_type(key, phitype, phi)
    return phi

def merge_phi_dicts(phi1, phi2, in_place=True):
    """
    Merge phi2 into phi1. If in_place is True, modify phi1 directly.
    Otherwise, return a new dict and leave phi1 unmodified.
    """
    if in_place:
        for key, types in phi2.items():
            if key in phi1:
                phi1[key].extend(t for t in types if t not in phi1[key])
            else:
                phi1[key] = types.copy()
        return phi1
    else:
        # start from a shallow copy of phi1
        merged = {k: v.copy() for k, v in phi1.items()}
        for key, types in phi2.items():
            if key in merged:
                merged[key].extend(t for t in types if t not in merged[key])
            else:
                merged[key] = types.copy()
        return merged

def is_medical_eponym(x):
    return x is not None and x.lower() in eponym_indicators


def is_name_indicator(x):
    return x is not None and x.lower() in name_indicators


def is_common(x):
    return x is not None and (
        x.upper() in common_words or x.upper() in unambig_common_words
    )


def is_commonest(x):
    return x is not None and (x.upper() in very_common_words or is_unambig_common(x))


def is_unambig_common(x):
    return x is not None and x.upper() in unambig_common_words


def is_probably_measurement(x):
    measurement_indicators = [
        "increased to",
        "decreased from",
        "rose to",
        "fell from",
        "down to",
        "increased from",
        "dropped to",
        "dec to",
        "changed to",
        "remains on",
        "change to",
    ]

    for indicator in measurement_indicators:
        if re.search(indicator, x, re.IGNORECASE):
            return True

    return False


def phi_dict_to_list(x, phi):
    phis = []

    for key in sorted(phi.keys(), key=lambda x: x.start):
        phis.append(
            {
                "phi_start": key.start,
                "phi_end": key.end,
                "phi": key.phi,
                "types": phi[key],
            }
        )

    return phis
