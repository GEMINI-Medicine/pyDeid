import re
import calendar
import random
import string
from phi_types.dates import months, days
from phi_types.utils import common_words
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

    if month is not None:
        old_month = months[month] if month in months else date.month
        number_of_days = days[str(old_month)]

    if day is not None:
        day = day + day_shift

        if month is not None:
            if day > number_of_days:
                month = month + 1
                day = day % number_of_days
        else:
            day = day % 31
    else:
        day = ""
    
    if month is not None:
        month = old_month + month_shift

        if month > 12:
            month = month % 12
            if year is not None:
                year = year + 1
    else:
        month = ""
    
    if year is not None:
        year = year + year_shift
    else:
        year = ""
        
    return str(day) + "-" + calendar.month_name[month] + "-" + str(year)


def time_shifter(time, hour_shift, minute_shift, second_shift):
    hours = time.hours
    minutes = time.minutes
    seconds = time.seconds
    meridiem = time.meridiem

    if time.seconds is not None: # seconds is optional as per the regex
        seconds = seconds + second_shift

        if seconds > 60 and minutes is not None:
            minutes = minutes + 1
    
    minutes = minutes + minute_shift

    if minutes > 60 and hours is not None:
        hours = hours + 1

    hours = hours + hour_shift

    if meridiem is not None:
        if hours > 12:
            hours = hours % 12

            if re.search(r'am|a.m.', meridiem, re.IGNORECASE):
                meridiem = ' p.m.'
            elif re.search(r'am|a.m.', meridiem, re.IGNORECASE):
                meridiem = ' a.m.'
            else:
                meridiem = " " + meridiem
    else:
        meridiem = ""

    return str(hours) + ":" + str(minutes) + ":" + str(seconds) + meridiem


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
    
    for key in sorted(phi.keys()):
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
                surrogate = random.choice(tuple(all_first_names))
            
            elif re.search('Last Name', val):
                surrogate = random.choice(tuple(all_last_names))
            
            elif re.search('Name Prefix', val):
                surrogate = ""
            
            elif re.search('Name', val): # not sure if first or last name, replace with first name
                surrogate = random.choice(tuple(all_first_names))
            
            elif re.search('Postalcode', val):
                surrogate = generate_postal_code()
            
            elif re.search(r'day|month|year', val, re.IGNORECASE):
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
