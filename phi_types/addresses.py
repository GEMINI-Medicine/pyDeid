import re
from phi_types.utils import is_unambig_common, add_type, PHI


apt_indicators = ["apt", "suite"] #only check these after the street address is found
street_add_suff = ["park", "drive", "street", "road", "lane", "boulevard", "blvd", "avenue", "highway", "circle","ave", "place", "rd", "st"]

# Strict street address suffix: case-sensitive match on the following, 
#     and will be marked as PHI regardless of ambiguity (common words)
strict_street_add_suff = ["Park", "Drive", "Street", "Road", "Lane", "Boulevard", "Blvd", "Avenue", "Highway","Ave", "Rd", "PARK", "DRIVE", "STREET", "ROAD", "LANE", "BOULEVARD", "BLVD", "AVENUE", "HIGHWAY","AVE", "RD"]

def address(x, phi):
    
    for suff in strict_street_add_suff:
        
        for m in re.finditer(r'\b(([0-9]+ +)?(([A-Za-z\.\']+) +)?([A-Za-z\.\']+) +\b' + suff + r'\.?\b)\b', x):
            start = m.start()
            end = m.end()
            
            next_seg = x[end:]
            
            for ind in apt_indicators:
                
                apt = re.search(r'^\b(' + ind + r'\.?\#? +[\w]+)\b', next_seg)

                if apt:
                    end = end + apt.end()

            if len(m.group(3)) == 0:
                if is_unambig_common(m.group(5)):
                    add_type(PHI(start, end, x[start:end]), 'Street Address', phi)
                    
            elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                add_type(PHI(start, end, x[start:end]), 'Street Address', phi)
                
    for suff in street_add_suff:
        
        for m in re.finditer(r'\b(([0-9]+) +(([A-Za-z]+) +)?([A-Za-z]+) +' + suff + r')\b', x, re.IGNORECASE):
            
            if m.group(3) is not None and len(m.group(3)) == 0:
                if is_unambig_common(m.group(5)):
                    add_type(PHI(m.start(), m.end(), m.group()), 'Street Address', phi)
                    
            elif not (is_unambig_common(m.group(4)) or is_unambig_common(m.group(5))):
                add_type(PHI(m.start(), m.end(), m.group()), 'Street Address', phi)


def postal_code(x, phi):
    for m in re.finditer(r'\b([a-zA-Z]\d[a-zA-Z][ \-]?\d[a-zA-Z]\d)\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'Postalcode', phi)
