import sys
sys.path.append('../')

import re
from .utils import *
import pkg_resources

from collections import defaultdict

DATA_PATH = pkg_resources.resource_filename('pyDeid', 'wordlists/')

female_names_unambig = load_file(os.path.join(DATA_PATH, 'female_names_unambig_v2.txt'))
male_names_unambig = load_file(os.path.join(DATA_PATH, 'male_names_unambig_v2.txt'))
all_first_names = load_file(os.path.join(DATA_PATH, 'all_first_names.txt'))

last_names_unambig = load_file(os.path.join(DATA_PATH, 'last_names_unambig_v2.txt'))
all_last_names = load_file(os.path.join(DATA_PATH, 'all_last_names.txt'))

doctor_first_names = load_file(os.path.join(DATA_PATH, 'doctor_first_names.txt'), optimization='iteration')
doctor_last_names = load_file(os.path.join(DATA_PATH, 'doctor_last_names.txt'))

female_names_ambig = load_file(os.path.join(DATA_PATH, 'female_names_ambig.txt'))
male_names_ambig = load_file(os.path.join(DATA_PATH, 'male_names_ambig.txt'))
last_names_ambig = load_file(os.path.join(DATA_PATH, 'last_names_ambig.txt'))

female_names_popular = load_file(os.path.join(DATA_PATH, 'female_names_popular_v2.txt'))
male_names_popular = load_file(os.path.join(DATA_PATH, 'male_names_popular_v2.txt'))
last_names_popular = load_file(os.path.join(DATA_PATH, 'last_names_popular_v2.txt'))

medical_phrases = load_file(os.path.join(DATA_PATH, 'medical_phrases.txt'), optimization='iteration')


namesets = [ # do this only once
    (female_names_unambig, 'Female First Name (un)'), 
    (male_names_unambig, 'Male First Name (un)'),
    (last_names_unambig, 'Last Name (un)'),
    (doctor_last_names, 'Doctor Last Name'),
    (female_names_ambig, 'Female First Name (ambig)'),
    (male_names_ambig, 'Male First Name (ambig)'),
    (last_names_ambig, 'Last Name (ambig)'),
    (female_names_popular, 'Female First Name (popular/ambig)'),
    (male_names_popular, 'Male First Name (popular/ambig)'),
    (last_names_popular, 'Last Name (popular/ambig)')
    # TODO: add patients here
]


def name_first_pass(
    x, 
    custom_dr_first_names = None, custom_dr_last_names = None, custom_patient_first_names = None, custom_patient_last_names = None
    ):
    """Find first matches of names against the notes and the wordlists"""
    res = {}
    word_pattern = re.compile('\w+')

    custom_names = []

    if custom_dr_first_names is not None:
        custom_names.append(({name.upper() for name in custom_dr_first_names}, 'Custom Doctor First Name'))
    if custom_dr_last_names is not None:
        custom_names.append(({name.upper() for name in custom_dr_last_names}, 'Custom Doctor Last Name'))
    if custom_patient_first_names is not None:
        custom_names.append(({name.upper() for name in custom_patient_first_names}, 'Custom Patient First Name'))
    if custom_patient_last_names is not None:
        custom_names.append(({name.upper() for name in custom_patient_last_names}, 'Custom Patient Last Name'))

    for word in word_pattern.finditer(x):
        for names, tag in namesets:
            if word.group().upper() in names:
                res.setdefault(PHI(word.start(), word.end(), word.group()),[]).append(tag)
        for names, tag in custom_names:
            if (
                word.group().upper() in names and 
                len(word.group().upper()) > 1 and
                not is_common(word.group()) and 
                not is_commonest(word.group()) and 
                not is_unambig_common(word.group())
                ): # reduces false positives for initials in custom names
                res.setdefault(PHI(word.start(), word.end(), word.group()),[]).append(tag)
    
    for phrase in medical_phrases:
        for m in re.finditer(phrase, x, re.IGNORECASE):
            res.setdefault(PHI(m.start(), m.end(), m.group()),[]).append('MedicalPhrase')

    for name in doctor_first_names:
        for m in re.finditer(name, x, re.IGNORECASE):
            res.setdefault(PHI(m.start(), m.end(), m.group()),[]).append('Doctor First Name')

    return res


def is_probably_name(key, phi):
    
    if (
        not is_common(key.phi) or 
        (is_type(key, "Name", True, phi) and is_type(key, "(un)", True, phi)) or 
        (is_type(key, "Name", True, phi) and (re.search(r'\b(([A-Z])([a-z]+))\b', key.phi) or re.search('\b(([A-Z]+))\b', key.phi)) or
        is_type(key, "popular", True, phi))
    ):
        return True
    else:
        return False


def combine_prefix_and_lastname(phi):
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
            
            if last_name_start < prefix_end + 3: # don't catch last names that occur way after
            
                prefix_start = first_word_key.start
                last_name_end = second_word_key.end

                combined_prefix_and_lastname = first_word_key.phi + second_word_key.phi
            
                add_type(PHI(prefix_start, last_name_end, combined_prefix_and_lastname), "Last Name", phi)


def follows_name_indicator(x, phi):
    for indicator in name_indicators:
        for m in re.finditer(r'\b(' + indicator + r')(s)?( *)(\-|\,|\.|\()?(  *)([A-Za-z]+\b)\b', x, re.IGNORECASE):
            start = m.start(6)
            end = m.end(6)
            
            key = PHI(start, end, m.group(6))
            
            if is_probably_name(key, phi):
                add_type(key, "Name (follows name indicator)", phi)
                
            string_after = x[end:]
            
            for n in re.finditer(r'^\b(and )?( *)([A-Za-z]+)\b', string_after, re.IGNORECASE):
                word_after = n.group(3)
                key_after = PHI(end + n.start(3), end + n.end(3), word_after)
                
                if (
                    not is_medical_eponym(word_after) and (
                        not is_name_indicator(word_after) and (
                            not is_common(word_after) or (
                                (is_type(key_after, "Name", True, phi) and is_type(key_after, "\(un\)", True, phi)) or (
                                is_type(key_after, "Name", True, phi) and re.search(r'\b(([A-Z])([a-z]+))\b', word_after)
                            ) or (
                                not is_commonest(word_after) and is_type(key_after, "Name", True, phi)
                            ) or
                            is_type(key_after, "popular", True, phi)
                            )
                        )
                    )
                ):
                    if not re.search(r'\b[\d]\b', string_after):
                        add_type(
                            key_after, 
                            "Name (follows name indicator)", 
                            phi
                            )
                        
                elif re.search(r'and', m.group(1)) and not is_medical_eponym(word_after):
                    if not (is_common(word_after) or is_name_indicator(word_after)):
                        add_type(
                            key_after, 
                            "Name (follows name indicator)", 
                            phi
                            )


def lastname_comma_firstname(x, phi):
    for m in re.finditer(r'\b([A-Za-z]+)( ?\, ?)([A-Za-z]+)\b', x, re.IGNORECASE):
        start_1 = m.start(1)
        end_1 = m.end(1)
        
        start_2 = m.start(3)
        end_2 = m.end(3)
        
        key_1 = PHI(start_1, end_1, m.group(1))
        key_2 = PHI(start_2, end_2, m.group(3))
        
        if (is_type(key_2, "Name", True, phi) and is_type(key_1, "Name (ambig)", True, phi) and not is_name_indicator(m.group(1))):
            add_type(key_1, "Last Name (lastname comma firstname)", phi)
            add_type(key_2, "First Name (lastname comma firstname)", phi)
            
        if is_type(key_2, "First Name", True, phi):
            
            if (
                is_type(key_1, "Last Name", True, phi) and not is_commonest(m.group(1)) and not is_name_indicator(m.group(1))
            ) or (
                not is_common(m.group(1)) and not is_commonest(m.group(1))
            ):
                add_type(key_1, "Last Name (lastname comma firstname)", phi)
                add_type(key_2, "First Name (lastname comma firstname)", phi)


def multiple_names_following_title(x, phi):
    plural_titles = ["doctors", "drs", "drs\.", "professors"]
    
    for title in plural_titles:
        for m in re.finditer(r'\b(((' + title + r' +)([A-Za-z]+) *(and +)?\,? *)([A-Za-z]+) *(and +)?\,? *)([A-Za-z]+)?\b', x, re.IGNORECASE):
            keys = []
            
            name1 = m.group(4)
            keys.append(PHI(m.start(4), m.end(4), name1))
            
            name2 = m.group(6)
            if (name2 is not None):
                keys.append(PHI(m.start(6), m.end(6), name2))
            
            name3 = m.group(8)
            if (name3 is not None):
                keys.append(PHI(m.start(8), m.end(8), name3))
                
            for key in keys:
                if (not is_commonest(key[2])) or is_type(key, "Name", True, phi):
                    add_type(key, "Name (multiple names following title)", phi)


def followed_by_md(x, phi):
    for m in re.finditer(r'\b((([A-Za-z\']+|[A-Za-z]\.) +)?((\([A-Za-z\']+\)|[A-Za-z\']+|[A-Za-z]\.) +)?([A-Za-z\-\']+)((\, *)|(\s+))(rrt|md|m\.d\.|crt|np|rn|nnp|msw|r\.n\.|staff|fellow|resident|\(fellow\)|\(resident\)|\(staff\))(\.|\,)*)', x, re.IGNORECASE):      

        if not re.search(r"(m\.?d\.?\')", x) and not re.search(r'(m\.?d\.?s)', x):
            
            first_name = m.group(3)
            
            if first_name is not None:
                first_name_key = PHI(m.start(3), m.end(3), first_name)
                
                if len(first_name) == 1 or (len(first_name) == 2 and re.search(r'\b([A-Za-z])\.+\b', first_name, re.IGNORECASE)):
                    add_type(first_name_key, "Name Initial (followed by MD)", phi)
                elif is_probably_name(first_name_key, phi):
                    add_type(first_name_key, "Name (followed by MD)", phi)

            
            last_name = m.group(6)
            
            if last_name is not None:
                last_name_key = PHI(m.start(6), m.end(6), last_name)
                
                if is_probably_name(last_name_key, phi):
                    add_type(last_name_key, "Name (followed by MD)", phi)
            
            initials = m.group(5)
            
            if initials is not None and last_name is not None:
                initials_key = PHI(m.start(5), m.end(5), initials)
                
                if len(initials) == 1 or (len(initials) == 2 and re.search(r'\b([A-Za-z])\.+\b', initials)) or is_probably_prefix(initials):
                    add_type(initials_key, "Name Initial (followed by MD)", phi)
                    
                elif is_probably_name(initials_key, phi):
                    add_type(initials_key, "Name (followed by MD)", phi)


def follows_pcp_name(x, phi):
    names_pre = ["PCP", "physician", "provider", "created by"]
    
    for pre in names_pre:
        for m in re.finditer(r'\b((' + pre + r'( +name)?( +is)?\s\s*)([A-Za-z\-]+)((\s*\,*\s*)? *)([A-Za-z\-]+\.?)(((\s*\,*\s*)? *)([A-Za-z\-]+))?)\b', x, re.IGNORECASE):
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
                if len(key[2]) == 1 or re.search(r'\b([A-Za-z])\.\b', key[2]):
                    add_type(key, "Name Initial (follows PCP name)", phi)
                elif is_probably_name(key, phi):
                    add_type(key, "Name (follows PCP name)", phi)

        for m in re.finditer(r'\b((' + pre + r'( +name)?( +is)? ?([\#\:\-\=\.\,])+ *)([A-Za-z\-]+)((\s*\,*\s*)? *)([A-Za-z\-]+\.?)((\s*\,*\s*)? *)([A-Za-z\-]+)?)\b', x, re.IGNORECASE):
            
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
                if len(first_name) == 1 or re.search(r'\b([A-Za-z])\.\b', first_name, re.IGNORECASE):
                    add_type(first_name_key, "Name Initial (name is)", phi)
                    first_found = True
                    
                elif is_probably_name(first_name_key, phi):
                    add_type(first_name_key, "Name (name is)", phi)
                    first_found = True
                        
            if first_found:
                second_found = False
                
                if initials is not None:
                    if len(initials) == 2 or re.search(r'\b([A-Za-z])\.\b', initials, re.IGNORECASE):
                        add_type(initials_key, "Name Initial (name is)", phi)
                        second_found = True
                        
                    elif is_probably_name(initials_key, phi):
                        add_type(initials_key, "Name (name is)", phi)
                        second_found = True
                        
                    if second_found:
                        if last_name is not None:
                            if (len(last_name) == 1) or re.search(r'\b([A-Za-z])\.\b', last_name, re.IGNORECASE):
                                add_type(last_name_key, "Name Initial (name is)", phi)

                            elif is_probably_name(last_name_key, phi):
                                add_type(last_name_key, "Name (name is)", phi)


prefixes_unambig = set(line.strip() for line in open(os.path.join(DATA_PATH, 'prefixes_unambig.txt')))
last_name_prefixes = set(line.strip() for line in open(os.path.join(DATA_PATH, 'last_name_prefixes.txt')))


def is_probably_prefix(x):
    return x.upper() in prefixes_unambig


def prefixes(x, phi):
    # Van Der Meer
    for pre in prefixes_unambig:
        for m in re.finditer(r'\b((' + pre + r')([\s\'\-])+ *)([A-Za-z]+)\b', x, re.IGNORECASE):
            prefix_key = PHI(m.start(2), m.end(2), m.group(2))
            
            last_name = m.group(4)
            last_name_key = PHI(m.start(4), m.end(4), last_name)
            
            if (not is_commonest(last_name)) or is_type(last_name_key, "Name", True, phi):
                add_type(prefix_key, "Name Prefix (prefixes)", phi)
                add_type(last_name_key, "Last Name (prefixes)", phi)


def titles(x, phi):
    specific_titles = ["MR", "MISTER", "MS"]
    
    # Mr. Sanders
    for title in specific_titles:
        for m in re.finditer(r'\b(' + title + r'\.( *))([A-Za-z\'\-]+)\b', x, re.IGNORECASE):
            potential_name = m.group(3)
            start = m.start(3)
            end = start + len(potential_name)
            key = PHI(start, end, potential_name)
            
            if is_type(key, "Name", True, phi):
                add_type(key, "Name (specific title)", phi)
            elif not is_common(potential_name):
                add_type(key, "Name (specific title)", phi)
    
    strict_titles = ["Dr", "DRS", "Mrs"]
    
    for title in strict_titles:
        for m in re.finditer(r'\b(' + title + r'\b\.? *)([A-Za-z\'\-]+)( ?)(\')?( ?)([A-Za-z]+)?( ?)([A-Za-z]+)?\b', x, re.IGNORECASE):
            
            word = m.group(2)
            
            start = m.start(2)
            end = m.end(2)
            key = PHI(start, end, word)
            
            if word.upper() in last_name_prefixes:
                add_type(key, "Last Name (specific title)", phi)
                
                next_word = m.group(6)
                if next_word is not None:

                    if next_word.upper() in last_name_prefixes:
                        key = PHI(m.start(6), m.end(6), next_word)

                        add_type(key, "Last Name (specific title)", phi)
                        
                        if m.group(8) is not None:
                            key = PHI(m.start(8), m.end(8), m.group(8))
                            
                    else:
                        key = PHI(m.start(6), m.end(6), next_word)
                        
                        if is_probably_name(key, phi):
                            add_type(key, "Last Name (specific title)", phi)
                            
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
                    
            
            add_type(key, "Last Name (specific title)", phi)
            
            # Dr. John
            if is_type(key, "First Name", True, phi):
                add_type(key, "First Name (specific title)", phi)
                
            # Dr. John Smith
            if m.group(6) is not None:
                potential_last_name = m.group(6)
                potential_last_name_key = PHI(m.start(6), m.end(6), potential_last_name)
                
                if (
                    is_probably_name(potential_last_name_key, phi) or (not is_commonest(potential_last_name)) or
                    (is_type(potential_last_name_key, "Name", True, phi) and is_type(potential_last_name_key, "(un)", False, phi)) or
                    (is_type(potential_last_name_key, "Name", True, phi) and re.search(r'\b(([A-Z])([a-z]+))\b', potential_last_name))
                ):
                    add_type(potential_last_name_key, "Name (specific title)", phi)

    other_titles = ['MISTER', 'DOCTOR', 'DOCTORS', 'MISS', 'PROF', 'PROFESSOR', 'REV', 'RABBI', 'NURSE', 'MD', 'PRINCESS', 'PRINCE', 'DEACON', 'DEACONESS', 'CAREGIVER', 'PRACTITIONER', 'MR', 'MS', 'RESIDENT', 'STAFF', 'FELLOW']

    for title in other_titles:
        for m in re.finditer(r'\b(' + title + r'\b\.? ?)([A-Za-z]+) *([A-Za-z]+)?(\,)?\b', x, re.IGNORECASE):
            word = m.group(2)
            
            start = m.start(2)
            end = m.end(2)
            key = PHI(start, end, word)
            
            word_after = m.group(3)
            start_after = m.start(3)
            end_after = m.end(3)
            key_after = PHI(start_after, end_after, word_after)
            
            if word.upper in last_name_prefixes:
                add_type(key, "Last Name (titles)", phi)
                
                next_word = m.group(8)
                string_after = x[end:]
                
                search_after = re.search(r'^( ?)(\')?( ?)([A-Za-z]+)\b', string_after)
                    
                if search_after:
                    token = search_after.group(4)
                    token_start = end + search_after.start(4)
                    token_end = end + search_after.end(4)
                    
                    if token.upper in last_name_prefixes:
                        new_key = PHI(start, token_end, x[start:token_end])
                        add_type(new_key, 'Last Name (titles)', phi)
                        
                        string_after_after = x[token_end:]
                        
                        search_after_after = re.search(r'( ?' + token + '( ?))([A-Za-z]+)\b', string_after_after)
                        
                        if search_after_after is not None:
                            word = search_after_after.group(3)
                            new_end = token_end + search_after_after.end(3)
                            
                            key = PHI(token_end, new_end, x[start:new_end])
                    else:
                        new_key = PHI(token_start, token_end, token)
                        
                        if is_probably_name(new_key, phi) and len(token) > 1:
                            add_type(new_key, 'Last Name (titles)', phi)
            else:
                apostrophes = re.search(r'(\')?([A-Za-z]+)(\')?', word)
                
                if apostrophes.group(1) is not None:
                    word = apostrophes.group(1)
                    key = PHI(start + 1, end, word)
                    
                if apostrophes.group(1) is not None:
                    word = apostrophes.group(1)
                    key = PHI(start, end - 1, word)
                
            if word_after is not None:
                if (
                    (not is_medical_eponym(word_after)) and ((not is_commonest(word_after)) or
                    (is_type(key_after, 'Name', True, phi) and is_type(key_after, '(un)', False, phi)) or
                    (is_type(key_after, "Name", True, phi) and re.search(r'\b(([A-Z])([a-z]+))\b', word_after))) 
                ):
                    add_type(key_after, 'Last Name (titles)', phi)
                    add_type(key, 'First Name (titles)', phi)
            elif key in phi:
                if is_type(key, 'Name', True, phi) and is_probably_name(key, phi):
                    add_type(key, 'Last Name (titles)', phi)
            else:
                if (word is not None) and (not is_common(word)) and is_probably_name(key, phi):
                    add_type(key, 'Last Name (titles)', phi)
                else:
                    add_type(key, 'Last Name (titles, ambig)', phi)
                        

def follows_first_name(x, phi):
    for i in list(phi): # transform to list because we are 1. iterating, 2. modifying
        if (
            (is_type(i, "Male First Name", True, phi) or is_type(i, "Female First Name", True, phi)) and
            (is_type(i, "(un)", True, phi) or is_type(i, "pop", True, phi))
        ):
            string_after = x[i[1]:]
            
            no_middle_initial = re.search(r'^( +)([A-Za-z\']{2,})\b', string_after)
            
            if no_middle_initial:
                key = PHI(i[1] + no_middle_initial.start(2), i[1] + no_middle_initial.end(2), no_middle_initial.group(2))
                
                if key in phi:
                    if (is_type(key, "Name", True, phi) and (is_probably_name(key, phi))):
                        add_type(key, "Last Name (follows first name)", phi)
                        add_type(i, "First Name (followed by last name)", phi) # make it unambig
                
                elif is_probably_name(key, phi):
                    add_type(key, "Last Name (follows first name)", phi)
                    add_type(key, "First Name (followed by last name)", phi)
                    
                    middle_initial = re.search(r'^( +)([A-Za-z])(\.? )([A-Za-z\-][A-Za-z\-]+)\b', string_after)
                    
                    if middle_initial:
                        initial_start = i[1] + middle_initial.start(2)
                        initial_key = PHI(initial_start, initial_start + 1, middle_initial.group(2))
                        last_name = middle_initial.group(4)
                        last_name_key = PHI(i[1] + middle_initial.start(4), i[1] + middle_initial.end(4), last_name)
                        
                        if last_name_key in phi and not is_type(last_name_key, "Last Name", False, phi):
                            add_type(last_name_key, "Last Name (follows first name)", phi)
                            add_type(initial_key, "Initial (follows first name)", phi)
                            add_type(i, "First Name (followed by last name)", phi)
                            
                        else:
                            if re.search(r'( +)([A-Za-z])(\.? )([A-Za-z][A-Za-z]+)\b\s*', string_after):
                                add_type(last_name_key, "Last Name (follows first name)", phi)
                                add_type(initial_key, "Initial (follows first name)", phi)
                                add_type(i, "First Name (followed by last name)", phi)
                                
                            elif not is_commonest(last_name):
                                add_type(last_name_key, "Last Name (follows first name)", phi)
                                add_type(initial_key, "Initial (follows first name)", phi)
                                add_type(i, "First Name (followed by last name)", phi)


def precedes_last_name(x, phi):
    for i in list(phi): # transform to list because we are 1. iterating, 2. modifying
        if is_type(i, "Last Name", True, phi) and is_type(i, "(un)", True, phi):
            string_before = x[:i[0]]
            
            first_name_exists = re.search(r'\b([A-Za-z]+)( *)$', string_before)
            
            if first_name_exists:
                first_name = first_name_exists.group(1)
                first_name_key = PHI(first_name_exists.start(1), first_name_exists.end(1), first_name)
                
                if first_name_key in phi:
                    if is_type(first_name_key, "First Name", True, phi) and (not is_name_indicator(first_name)):
                        add_type(first_name_key, "First Name (precedes last name)", phi)
                
                elif not is_common(first_name):
                    add_type(first_name_key, "First Name (precedes last name)", phi)


def compound_last_names(x, phi):
    for i in list(phi): # transform to list because we are 1. iterating, 2. modifying
        string_after = x[i[1]:]
        
        if is_type(i, "Last Name", False, phi):
            
            hyphenated_last_name = re.search(r'^-([A-Za-z]+)\b', string_after)
                
            if hyphenated_last_name:
                add_type(PHI(i[1] + hyphenated_last_name.start(1), i[1] + hyphenated_last_name.end(1), hyphenated_last_name.group(1)), "Last Name (compound last name)", phi)
            
            double_last_name = re.search(r'^( *)([A-Za-z]+)\b', string_after)
            
            if double_last_name:
                last_name = double_last_name.group(2)
                last_name_key = PHI(i[1] + double_last_name.start(2), i[1] + double_last_name.end(2), last_name)
                
                if last_name_key in phi:
                    if not is_type(last_name_key, "ambig", True, phi) and not is_type(last_name_key, "Last Name", False, phi):
                        add_type(last_name_key, "Last Name (compound last name)", phi)
                
                elif not is_common(last_name):
                    add_type(last_name_key, "Last Name (compound last name)", phi)


def initials(x, phi):
    for i in list(phi): # transform to list because we are 1. iterating, 2. modifying
        if (not is_type(i, "ambig", True, phi) or is_type(i, "(un)", True, phi)) and is_type(i, "Name", True, phi):
            string_before = x[:i[0]]
            
            two_initials = re.search(r'\b([A-Za-z][\. ] ?[A-Za-z]\.?) ?$', string_before)
            single_initial = re.search(r'\b([A-Za-z]\.?) ?$', string_before)
            
            if two_initials:
                add_type(PHI(i[0] - len(two_initials.group()), i[0] - len(two_initials.group()) + len(two_initials.group(1)), two_initials.group(1)), "Initials (double)", phi)
            elif single_initial:
                initial = single_initial.group(1)
                initial_key = PHI(i[0] - len(single_initial.group()), i[0] - len(single_initial.group()) + len(single_initial.group(1)), single_initial.group(1))
                
                if len(initial) == 2 or len(initial) == 1:
                    add_type(initial_key, "Initials (single)", phi)
                if not is_type(i, "Last Name", 0, phi):
                    add_type(i, "Last Name (single)", phi)
                    
        if is_type(i, "Last Name", True, phi) and not is_type(i, "ambig", True, phi):
            string_before = x[:i[0]]
            
            two_initials = re.search(r'\b([A-Za-z][\. ] ?[A-Za-z]\.?) ?$', string_before)
            single_initial = re.search(r'\b([A-Za-z]\.?) ?$', string_before)
            
            if two_initials:
                add_type(PHI(i[1] + two_initials.start(1), i[1] + two_initials.end(1), two_initials.group(1)), "Initials (double)", phi)
                
                if not is_type(i, "Last Name", False, phi):
                    add_type(i, "Last Name (follows initials)", phi)
                    
            elif single_initial:
                initial = single_initial.group(1)
                initial_key = PHI(i[1] + single_initial.start(1), i[1] + single_initial.end(1), initial)


def list_of_names(x, phi):
    for i in list(phi): # transform to list because we are 1. iterating, 2. modifying
        if is_type(i, "Last Name", False, phi) or is_type(i, "Male First Name", False, phi) or is_type(i, "Female First Name", False, phi):
            string_after = x[i[1]:]
            
            and_or = re.search(r'^ or|and ([A-Za-z]+)\b', string_after, re.IGNORECASE)
            and_or_symbols = re.search(r'^( ?[\&\+] ?)([A-Za-z]+)\b', string_after, re.IGNORECASE)
            three_names = re.search(r'^, ([A-Za-z]+)(,? and )([A-Za-z]+)\b', string_after, re.IGNORECASE)
            
            if and_or:
                name = and_or.group(1)
                name_key = PHI(i[1] + and_or.start(1), i[1] + and_or.end(1), name)
                
                if is_type(name_key, "Name", True, phi) or is_common(name):
                    add_type(name_key, "Name (list of names)", phi)
                    
            elif and_or_symbols:
                name = and_or_symbols.group(2)
                name_key = PHI(i[1] + and_or_symbols.start(2), i[1] + and_or_symbols.end(2), name)
                
                if not is_common(name):
                    add_type(name_key, "Name (list of names)", phi)
                    
            elif three_names:
                name1 = three_names.group(1)
                name2 = three_names.group(3)
                
                name1_key = PHI(i[1] + three_names.start(1), i[1] + three_names.end(1), name1)
                name2_key = PHI(i[1] + three_names.start(3), i[1] + three_names.end(3), name2)
                
                if not is_common(name1):
                    add_type(name1_key, "Name (list of names)", phi)
                if not is_common(name2):
                    add_type(name2_key, "Name (list of names)", phi)

def ner(x, phi, model):
    res = model(x)

    for ent in res.ents:
        if ent.label_ == 'PERSON':
            # check for firstname lastname
            m = re.search(r'(.*)\s(.*)', ent.text)
            if m is not None:
                add_type(PHI(ent.start_char, ent.start_char + m.end(1), m.group(1)), "First Name (NER)", phi)
                add_type(PHI(ent.start_char + m.start(2), ent.end_char, m.group(2)), "Last Name (NER)", phi)
            else:
                add_type(PHI(ent.start_char, ent.end_char, ent.text), "Name (NER)", phi)

def recurring_name(phi):
    # Step 1: Count occurrences of each phi value
    phi_count = defaultdict(int)
    for key, value in phi.items():
        if any("Name" in item for item in value):
            phi_count[key.phi] += 1
    
    # Step 2: Identify phi values that appear in 2 or more keys
    common_phis = {phi for phi, count in phi_count.items() if count >= 2}
    
    # Step 3: Modify the dictionary in place
    for key, value in phi.items():
        if key.phi in common_phis:
            value.append("Name (found multiple times)")
