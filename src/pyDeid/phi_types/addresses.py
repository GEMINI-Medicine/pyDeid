import re
from .utils import is_unambig_common, add_type, PHI
from .utils import load_file
import pkg_resources
import os

DATA_PATH = pkg_resources.resource_filename('pyDeid', 'wordlists/')

local_places_unambig = load_file(os.path.join(DATA_PATH, 'local_places_unambig_v2.txt'), optimization='iteration')
hospitals = load_file(os.path.join(DATA_PATH, 'ontario_hospitals.txt'), optimization='iteration')
hospital_acronyms = load_file(os.path.join(DATA_PATH, 'hospital_acronyms.txt'), optimization='iteration')

apt_indicators = ["apt", "suite"] #only check these after the street address is found
street_add_suff = ["park", "drive", "street", "road", "lane", "boulevard", "blvd", "avenue", "highway", "circle","ave", "place", "rd", "st"]


# Strict street address suffix: case-sensitive match on the following, 
#     and will be marked as PHI regardless of ambiguity (common words)
strict_street_add_suff = ["Park", "Drive", "Street", "Road", "Lane", "Boulevard", "Blvd", "Avenue", "Highway","Ave", "Rd", "PARK", "DRIVE", "STREET", "ROAD", "LANE", "BOULEVARD", "BLVD", "AVENUE", "HIGHWAY","AVE", "RD"]


def address(x, phi):

    for place in local_places_unambig:
        
        for m in re.finditer(place, x, re.IGNORECASE):
            add_type(PHI(m.start(), m.end(), m.group()), 'Location (un)', phi)
    
    for suff in strict_street_add_suff:
        
        for m in re.finditer(r'\b(([0-9]+ +)?(([A-Za-z\.\']+) +)?([A-Za-z\.\']+) +\b' + suff + r'\.?\b)\b', x):
            start = m.start()
            end = m.end()
            
            next_seg = x[end:]
            
            for ind in apt_indicators:
                
                apt = re.search(r'^\b(' + ind + r'\.?\#? +[\w]+)\b', next_seg)

                if apt:
                    end = end + apt.end()

            if m.group(3) is not None:
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


def hospital(x, phi):

    for hospital in hospitals:
        
        terms = hospital.split(" ")
        n_terms = len(terms)

        if n_terms == 1:
            for m in re.finditer(hospital, x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

        if n_terms == 2:
            for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + r')\b', x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

        if n_terms == 3:
            for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + r')\b', x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

        if n_terms == 4:
            for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + r')\b', x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

        if n_terms == 5:
            for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + ')\s(' + terms[4] + r')\b', x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

        if n_terms == 6:
            for m in re.finditer(r'\b(' + terms[0] + ')\s(' + terms[1] + ')\s(' + terms[2] + ')\s(' + terms[3] + ')\s(' + terms[4] + ')\s(' + terms[5] + r')\b', x, re.IGNORECASE):
                add_type(PHI(m.start(), m.end(), m.group()), 'Hospital', phi)

    for acronym in hospital_acronyms:
        for m in re.finditer(acronym, x):
            add_type(PHI(m.start(), m.end(), m.group()), 'Site Acronym', phi)
