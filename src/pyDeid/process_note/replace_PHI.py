import sys
sys.path.append('../')

import re
import calendar
import random
import string
from phi_types.dates import months, days, Date
from phi_types.utils import just_common_words
from phi_types.names import all_first_names, all_last_names
from phi_types.contact_info import canadian_area_codes
from phi_types.addresses import strict_street_add_suff, local_places_unambig


def generate_postal_code():
    letters = random.choices(string.ascii_uppercase, k = 3)
    numbers = random.choices(string.digits, k = 3)

    res = ""

    for i in range(3):
        res = res + letters[i] + numbers[i]

    return res


def date_shifter(date, day_shift, month_shift, year_shift):
    
    day = date.day
    month = date.month
    year = date.year

    res = ''

    if date.month is not None:
        old_month = months[month] if month in months else int(month)
        number_of_days = days[str(old_month)]

    if day is not None:
        day = int(day) + day_shift

        if old_month is not None:
            if int(day) > number_of_days:
                month = int(old_month) + 1
                day = int(day) % number_of_days
        else:
            day = int(day) % 31
    
    if month is not None:
        month = int(old_month) + month_shift

        if int(month) > 12:
            month = int(month) % 12
            if year is not None:
                year = int(year) + 1

        month = calendar.month_name[month]
    
    if year is not None:
        year = int(year) + year_shift
        
    return '-'.join([str(component) for component in [day, month, year] if component])


def time_shifter(time, hour_shift, minute_shift, second_shift):
    hours = time.hours
    minutes = time.minutes
    seconds = time.seconds
    meridiem = time.meridiem

    if seconds is not None: # seconds is optional as per the regex
        seconds = int(seconds) + second_shift

        if int(seconds) > 60 and minutes is not None:
            seconds = int(seconds) % 60
            minutes = int(minutes) + 1
    else:
        seconds = "00"
    
    if minutes is not None:
        minutes = int(minutes) + minute_shift

        if int(minutes) > 60 and hours is not None:
            minutes = int(minutes) % 60
            hours = int(hours) + 1
    else:
        minutes = "00"

    if hours is not None:
        hours = int(hours) + hour_shift
    else:
        hours = "00"

    if meridiem is not None and hours != "":
        if int(hours) > 12:
            hours = int(hours) % 12

            if re.search(r'am|a.m.', meridiem, re.IGNORECASE):
                meridiem = ' p.m.'
            elif re.search(r'pm|p.m.', meridiem, re.IGNORECASE):
                meridiem = ' a.m.'
            else:
                meridiem = " " + meridiem
        else:
            meridiem = " " + meridiem
    else:
        if int(hours) > 24:
            hours = int(hours) % 24
        meridiem = ""

    return str(hours) + ":" + str(minutes) + ":" + str(seconds) + meridiem


def build_email():
    local_part = re.sub("[^a-zA-Z]+", "", random.choice(tuple(just_common_words)))
    domain = re.sub("[^a-zA-Z]+", "", random.choice(tuple(just_common_words)))

    return local_part + "@" + domain + ".com"


def build_telephone():
    return random.choice(tuple(canadian_area_codes)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(1000, 9999))


def build_address():
    return str(random.randint(1000, 9999)) + ' ' + random.choice(tuple(all_first_names)) + ' ' + random.choice(strict_street_add_suff)


def build_ohip():
    return str(random.randint(1000, 9999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))


def build_sin():
    return str(random.randint(100, 999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))


def replace_phi(x, phi, return_surrogates = False):
    deid_text = ""
    surrogates = []
    where_we_left_off = 0
    
    # keep a consistent date shift so all dates maintain relative distace
    day_shift = random.randint(0, 29)
    month_shift = random.randint(0, 11)
    year_shift = random.randint(-30, 30)

    # similarly for time shift
    hour_shift = random.randint(0, 11)
    minute_shift = random.randint(0, 59)
    second_shift = random.randint(0, 59)
    
    for key in sorted(phi.keys(), key = lambda x: x.start):
        for val in phi[key]:
            
            if re.search('MRN', val):
                surrogate = str(random.randint(0, 10**7))
                
            elif re.search('SIN', val):
                surrogate = build_sin()
            
            elif re.search('OHIP', val):
                surrogate = build_ohip()
            
            elif re.search('Telephone/Fax', val):
                surrogate = build_telephone()
            
            elif re.search('Email Address', val):
                surrogate = build_email()
            
            elif re.search('Address', val):
                surrogate = build_address()

            elif re.search('Location', val):
                surrogate = random.choice(tuple(local_places_unambig))
            
            elif re.search('First Name', val):
                surrogate = random.choice(tuple(all_first_names)).title()
            
            elif re.search('Last Name', val):
                surrogate = random.choice(tuple(all_last_names)).title()
            
            elif re.search('Name Prefix', val):
                surrogate = ""
            
            elif re.search('Name', val): # not sure if first or last name, replace with first name
                surrogate = random.choice(tuple(all_first_names)).title()
            
            elif re.search('Postalcode', val):
                surrogate = generate_postal_code()
            
            elif re.search(r'day|month|year', val, re.IGNORECASE):
                if isinstance(key.phi, Date):
                    surrogate = date_shifter(key.phi, day_shift, month_shift, year_shift)

            elif re.search('Time', val, re.IGNORECASE):
                surrogate = time_shifter(key.phi, hour_shift, minute_shift, second_shift)

            elif re.search('Holiday', val):
                surrogate = ""
            
            else:
                surrogate = '<PHI>'
        
            # TODO: Initials? Date range? Not in original
        
            if surrogate != '<PHI>': # for multiple PHI types for a single token, just pick one
                break
        
        deid_text = deid_text + x[where_we_left_off:key.start] + surrogate
        
        if return_surrogates:
            surrogate_start = len(deid_text) - 1
            surrogate_end = surrogate_start + len(surrogate)

            surrogates.append({
                'phi_start': key.start,
                'phi_end': key.end,
                'phi': key.phi,
                'surrogate_start': surrogate_start,
                'surrogate_end': surrogate_end ,
                'surrogate': surrogate,
                'types': phi[key]
                })
            
        where_we_left_off = key.end
    
    deid_text = deid_text + x[where_we_left_off:]
    
    return (surrogates, deid_text)