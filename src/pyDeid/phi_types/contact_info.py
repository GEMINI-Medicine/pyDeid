import re
from .utils import load_file, add_type, PHI
import pkg_resources
import os

DATA_PATH = pkg_resources.resource_filename('pyDeid', 'wordlists/')

def email(x, phi):
    for m in re.finditer(r'\b([\w\.]+\w ?@ ?\w+[\.\w+]((\.\w+)?){,3}\.\w{2,3})\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'Email Address', phi)


area_codes = load_file(os.path.join(DATA_PATH, 'US/area_codes.txt'))
phone_disqualifiers = ["HR","Heart", "BP", "SVR", "STV", "VT", "Tidal Volumes", "Tidal Volume", "TV", "CKS"]


def is_common_area_code(x):
    return x in area_codes


def is_probably_phone(x):
    for i in phone_disqualifiers:
        if re.search(r'\b' + i + r'\b'):
            return False
    return True


def telephone_match(x, m):
    
    start = m.start()
    end = m.end()

    next_seg = x[end:]

    extension = re.search(r'^(\s*(x|ex|ext|extension)\.?\s*[\(]?[\d]+[\)]?)\b', next_seg, re.IGNORECASE)

    if extension:
        end = end + extension.end()
        
    return PHI(start, end, x[start:end])

def telephone(x, phi):
    
    # ###-###-#### (potentially with arbitrary line breaks)
    # accept number with line breaks only if it starts with a valid area code
    for m in re.finditer(r'\(?(\d{3})\s*[\)\.\/\-\, ]*\s*\d\s*\d\s*\d\s*[ \-\.\/]*\s*\d\s*\d\s*\d\s*\d', x): # prepend all regex w/ '\(?' outside of testing
        
        if re.search(r'\(?\d{3}\s*[\)\.\/\-\, ]*\s*\d{3}\s*[ \-\.\/]*\s*\d{4}', m.group()):
            add_type(telephone_match(x, m), 'Telephone/Fax', phi)
        elif is_common_area_code(m.group(1)):
            add_type(telephone_match(x, m), 'Telephone/Fax', phi)
    
    # ###-###-###
    for m in re.finditer(r'\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{3}\b', x):
        if is_common_area_code(m.group(1)):
            add_type(telephone_match(x, m), 'Telephone/Fax', phi)
    
    # this will always create multiple matches with pattern 1, its ok, double obscure it.
    # ###-###-#####
    for m in re.finditer(r'\(?(\d{3})\s*[\)\.\/\-\=\, ]*\s*\d{3}\s*[ \-\.\/\=]*\s*\d{5}\b', x):
        if is_common_area_code(m.group(1)):
            add_type(telephone_match(x, m), 'Telephone/Fax', phi)
    
    # ###-####-###
    for m in re.finditer(r'\(?\d{3}?\s?[\)\.\/\-\=\, ]*\s?\d{4}\s?[ \-\.\/\=]*\s?\d{3}\b', x):
        add_type(telephone_match(x, m), 'Telephone/Fax', phi)
