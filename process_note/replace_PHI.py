import re
import calendar
from collections import namedtuple
import random
import string
from phi_types.dates import months
from phi_types.utils import common_words
from phi_types.names import all_first_names, all_last_names
from phi_types.contact_info import canadian_area_codes
from phi_types.addresses import strict_street_add_suff


Surrogate = namedtuple("Surrogate", ["phi_start", "phi_end", "phi", "replacement_start", "replacement_end", "replacement"])

def generate_postal_code():
    letters = random.choices(string.ascii_uppercase, k = 3)
    numbers = random.choices(string.digits, k = 3)

    res = ""

    for i in range(3):
        res = res + letters[i] + numbers[i]

    return res

def date_shifter(date, day_shift, month_shift, year_shift):
    
    if date.day is not None:
        day = (date.day + day_shift) % 30
    else:
        day = ""
    
    if date.month is not None:
        old_month = months[date.month] if date.month in months else date.month
        month = (old_month + month_shift) % 12
    else:
        month = ""
    
    if date.year is not None:
        year = date.year + year_shift
    else:
        year = ""
    
    if month != "" and day != "" and month == 2 and day > 28: # fix feb 28th
        day = 28
        
    return str(day) + "-" + calendar.month_name[month] + "-" + str(year)

def build_email():
    return random.choice(tuple(common_words)) + "@" + random.choice(tuple(common_words)) + ".com"

def build_telephone():
    return random.choice(tuple(canadian_area_codes)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(1000, 9999))

def build_address():
    return str(random.randint(1000, 9999)) + ' ' + random.choice(tuple(all_first_names)) + ' ' + random.choice(strict_street_add_suff)

def build_ohip():
    return str(random.randint(1000, 9999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))

def build_sin():
    return str(random.randint(100, 999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))


def replace_phi(x, phi, return_replacements = False):
    deid_text = ""
    replacements = {}
    where_we_left_off = 0
    
    # keep a consistent date shift so all dates maintain relative distace
    day_shift = random.randint(0, 29)
    month_shift = random.randint(0, 11)
    year_shift = random.randint(-30, 30)
    
    for key in sorted(phi.keys()):
        for val in phi[key]:
            
            if re.search('MRN', val):
                replacement = str(random.randint(0, 10**7))
                
            elif re.search('SIN', val):
                replacement = build_sin()
            
            elif re.search('OHIP', val):
                replacement = build_ohip()
            
            elif re.search('Telephone/Fax', val):
                replacement = build_telephone()
            
            elif re.search('Email Address', val):
                replacement = build_email()
            
            elif re.search('Address', val):
                replacement = build_address()
            
            elif re.search('First Name', val):
                replacement = random.choice(tuple(all_first_names))
            
            elif re.search('Last Name', val):
                replacement = random.choice(tuple(all_last_names))
            
            elif re.search('Name Prefix', val):
                replacement = ""
            
            elif re.search('Name', val): # not sure if first or last name, replace with first name
                replacement = random.choice(tuple(all_first_names))
            
            elif re.search('Postalcode', val):
                replacement = generate_postal_code()
            
            elif re.search(r'day|month|year', val, re.IGNORECASE):
                replacement = date_shifter(key.phi, day_shift, month_shift, year_shift)
                
            elif re.search('Holiday', val):
                replacement = ""
            
            else:
                replacement = '<PHI>'
        
            # TODO: Initials? Date range? Not in original
        
            if replacement != '<PHI>': # for multiple PHI types for a single token, just pick one
                break
        
        deid_text = deid_text + x[where_we_left_off:key.start] + replacement
        
        if return_replacements:
            
            replacement_start = len(deid_text) - 1
            replacement_end = replacement_start + len(replacement)
            replacements.setdefault(Surrogate(key.start, key.end, key.phi, replacement_start, replacement_end, replacement), phi[key])
            
        where_we_left_off = key.end
    
    deid_text = deid_text + x[where_we_left_off:]
    
    if replacements:
        return (replacements, deid_text)
    else:
        return deid_text
