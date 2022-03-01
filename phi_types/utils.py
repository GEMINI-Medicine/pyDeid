import re
from collections import namedtuple


PHI = namedtuple("PHI", ["start", "end", "phi"])

name_indicators = ["problem","problem:", "proxy", "fellow", "staff", "(fellow)","(staff)", "daughter","daughters", "dtr", "son", "brother","sister", "mother", "mom", "father", "dad", "wife", "husband", "neice", "nephew", "spouse", "partner", "cousin", "aunt", "uncle", "granddaughter", "grandson", "grandmother", "grandmom", "grandfather", "granddad", "relative", "friend", "neighbor", "visitor", "family member", "lawyer", "priest", "rabbi", "coworker", "co-worker", "boyfriend", "girlfriend", "name is", "named", "rrt", "significant other", "jr", "caregiver", "proxys", "friends", "sons", "brothers", "sisters", "sister-in-law", "brother-in-law", "mother-in-law", "father-in-law", "son-in-law", "daughter-in-law", "dtr-in-law", "surname will be", "name will be", "name at discharge will be", "name at discharge is"]
eponym_indicators = ["disease", "cyst", "catheter", "syndrome", "tumour", "forceps", "boil", "method", "test", "sign", "abscess", "canal", "duct", "clamp", "effect", "law"]

def load_file(filename):
    return set(line.strip() for line in open(filename))

unambig_common_words = load_file('wordlists/notes_common.txt')

medical_words = load_file('wordlists/sno_edited.txt')
very_common_words = load_file('wordlists/commonest_words.txt')
just_common_words = load_file('wordlists/common_words.txt')

common_words = medical_words | very_common_words | just_common_words # TODO: Add medical words to common words


def is_type(key:str, phitype: str, pattern: bool, phi):
    types = phi.get(key)
    if types is not None:
        for val in phi.get(key):
            if pattern:
                if re.search(phitype, val):
                    return True
            else:
                return val == phitype
            

def add_type(key, phitype, phi): # TODO: Use sets for keys?
    phi.setdefault(key,[]).append(phitype)
    
    
def is_medical_eponym(x):
    return x is not None and x.upper() in eponym_indicators
    

def is_name_indicator(x):
    return x is not None and x.upper() in name_indicators
    

def is_common(x):
    return x is not None and (x.upper() in common_words or x.upper() in unambig_common_words)
    

def is_commonest(x):
    return x is not None and (x.upper() in very_common_words or is_unambig_common(x))


def is_unambig_common(x):
    return x is not None and x.upper() in unambig_common_words