import re
from phi_types.utils import load_file, add_type, PHI


def email(x, phi):
    for m in re.finditer(r'\b([\w\.]+\w ?@ ?\w+[\.\w+]\.\w{2,3})\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'Email Address', phi)


canadian_area_codes = load_file('wordlists/canadian_area_code.txt')
phone_disqualifiers = ["HR","Heart", "BP", "SVR", "STV", "VT", "Tidal Volumes", "Tidal Volume", "TV", "CKS"]


def is_common_area_code(x):
    return x in canadian_area_codes


def is_probably_phone(x):
    for i in phone_disqualifiers:
        if re.search(r'\b' + i + r'\b'):
            return False
    return True


def telephone_match(x, m):
    
    start = m.start()
    end = m.end()

    next_seg = x[end:]

    extension = re.search(r'^(\s*(x|ex|ext|extension)\.?\s*[\(]?[\d]+[\)]?)\b', next_seg)

    if extension:
        end = end + extension.end()
        
    return PHI(start, end, x[start:end])

def telephone(x, phi):
    
    # ###-###-#### (potentially with arbitrary line breaks)
    # accept number with line breaks only if it starts with a valid area code
    for m in re.finditer(r'\(*(\d{3})\s*[\)\.\/\-\, ]*\s*\d\s*\d\s*\d\s*[ \-\.\/]*\s*\d\s*\d\s*\d\s*\d', x):
        
        if re.search(r'\(*\d{3}\s*[\)\.\/\-\, ]*\s*\d{3}\s*[ \-\.\/]*\s*\d{4}', x):
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
