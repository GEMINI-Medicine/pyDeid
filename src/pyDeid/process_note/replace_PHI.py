import re
import calendar
import random
import string
from ..phi_types.dates import months, days, Date
from ..phi_types.utils import just_common_words, add_type
from ..phi_types.names import all_first_names, all_last_names
from ..phi_types.contact_info import canadian_area_codes
from ..phi_types.addresses import strict_street_add_suff, local_places_unambig


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
                old_month = int(old_month) + 1
                day = int(day) % number_of_days
        else:
            day = int(day) % 31
    
    if month is not None:
        month = int(old_month) + month_shift

        if int(month) > 12:
            month = int(month) % 12
            if year is not None:
                year = int(year) + 1
    
    if year is not None:
        year = int(year) + year_shift
        
    return day, month, year


def build_date(day, month, year, month_before_day, year_first, month_name, month_abbr, suffix, leading_zeros):

    if month:
        if month_name and month_abbr:
            month = calendar.month_abbr[month]
        elif month_name and not month_abbr:
            month = calendar.month_name[month]
        else:
            month = str(month)

        if len(month) == 1 and leading_zeros:
            month = '0' + month
    
    if year:
        if year < 40: # add century if necessary
            year = str(year + 2000)
        elif year >= 40 and year < 1000:
            year = str(year + 1900)
        else:
            year = str(year)

    if day:
        if suffix:
            if 4 <= day <= 20 or 24 <= day <= 30:
                day = str(day) + "th"
            else:
                day = str(day) + ["st", "nd", "rd"][day % 10 - 1]
        else:
            day = str(day)

        if len(day) == 1 and leading_zeros:
            day = '0' + day
    
    res = ''
    
    if not suffix:
        if month_name:
            sep = random.choice(['-', ' '])
        else:
            sep = random.choice(['-', ' ', '/'])
            
        if day and month and month_before_day:
            res = res + month + sep + day
        elif day and month:
            res = res + day + sep + month
        elif day and (not month):
            res = res + day
        elif month and (not day):
            res = res + month
        
        if year:
            if month or day:
                year_sep = random.choice(['. ', ', ', ' ']) if sep == ' ' else sep
            else:
                year_sep = ''

            if year_first:
                res = year + year_sep + res
            else:
                res = res + year_sep + year
            
    if suffix: # month_name must be true
            
        if day and month and month_before_day:
            res = day + ' of ' + month
            
            if year:
                year_sep = random.choice(['. ', ', ', ' '])
                res = res + year_sep + year
    
        elif day and year and (not month):
            res = day + ' of ' + year
            
        else:
            sep = random.choice(['-', ' '])
            
            if day and month and (not month_before_day):
                res = res + day + sep + month
            elif day and (not month):
                res = res + day
            elif month and (not day):
                res = res + month

            if year:
                if month or day:
                    year_sep = random.choice(['. ', ', ', ' ']) if sep == ' ' else sep
                else:
                    year_sep = ''

                if year_first:
                    res = year + year_sep + res
                else:
                    res = res + year_sep + year

    return res


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

    # configure surrogate date format (will be consistent within note)
    month_before_day = random.choice([True, False])
    year_first = random.choice([True, False])
    leading_zeros = random.choice([True, False])
    month_name = random.choice([True, False])
    
    if month_name:
        suffix = random.choice([True, False])
        month_abbr = random.choice([True, False])
    else:
        suffix = False
        month_abbr = False

    name_lookup = {}
    
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
                if key.phi not in name_lookup.keys():
                    name_lookup[key.phi] = random.choice(tuple(all_first_names)).title()

                surrogate = name_lookup[key.phi]
                
            elif re.search('Last Name', val):
                if key.phi not in name_lookup.keys():
                    name_lookup[key.phi] = random.choice(tuple(all_last_names)).title()

                surrogate = name_lookup[key.phi]
            
            elif re.search('Name Prefix', val):
                surrogate = ""
            
            elif re.search('Name', val): # not sure if first or last name, replace with first name
                if key.phi not in name_lookup.keys():
                    name_lookup[key.phi] = random.choice(tuple(all_first_names)).title()

                surrogate = name_lookup[key.phi]
            
            elif re.search('Postalcode', val):
                surrogate = generate_postal_code()
            
            elif re.search(r'day|month|year', val, re.IGNORECASE):
                if isinstance(key.phi, Date):
                    day, month, year = date_shifter(key.phi, day_shift, month_shift, year_shift)

                    surrogate = build_date(day, month, year, month_before_day, year_first, month_name, month_abbr, suffix, leading_zeros)
                else:
                    surrogate = '<PHI>'

            elif re.search('Time', val, re.IGNORECASE):
                surrogate = time_shifter(key.phi, hour_shift, minute_shift, second_shift)

            elif re.search('Holiday', val):
                surrogate = ""
            
            else:
                surrogate = '<PHI>'
        
            if surrogate != '<PHI>': # for multiple PHI types for a single token, just pick one
                break
        
        surrogate_start = len(deid_text + x[where_we_left_off:key.start])

        deid_text = deid_text + x[where_we_left_off:key.start] + surrogate
        
        if return_surrogates:
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

def return_phi(x, phi, return_surrogates = False):
    phis = []
    
    for key in sorted(phi.keys(), key = lambda x: x.start):        
        if return_surrogates:
            phis.append({
                'phi_start': key.start,
                'phi_end': key.end,
                'phi': key.phi,
                'types': phi[key]
                })
            
    return phis

def replace_value(val, val_type, note, phi):
    deid_text = note
    # surrogates = []
    # where_we_left_off = 0
    
    # keep a consistent date shift so all dates maintain relative distace
    day_shift = random.randint(0, 29)
    month_shift = random.randint(0, 11)
    year_shift = random.randint(-30, 30)

    # similarly for time shift
    hour_shift = random.randint(0, 11)
    minute_shift = random.randint(0, 59)
    second_shift = random.randint(0, 59)

    # configure surrogate date format (will be consistent within note)
    month_before_day = random.choice([True, False])
    year_first = random.choice([True, False])
    leading_zeros = random.choice([True, False])
    month_name = random.choice([True, False])
    
    if month_name:
        suffix = random.choice([True, False])
        month_abbr = random.choice([True, False])
    else:
        suffix = False
        month_abbr = False

    # name_lookup = {}

    if val_type == 'mrn':
        surrogate = str(random.randint(0, 10**7))
        
    # case 'sin':
    #     surrogate = build_sin()
    
    elif val_type == 'health_card_number':
        surrogate = build_ohip()
    
    # case re.search('telephone/fax', val):
    #     surrogate = build_telephone()
    
    # case re.search('email address', val):
    #     surrogate = build_email()
    
    # case re.search('address', val):
    #     surrogate = build_address()

    # case re.search('location', val):
    #     surrogate = random.choice(tuple(local_places_unambig))
    
    elif val_type == 'first_name':
        # if val.phi not in name_lookup.keys():
        surrogate = random.choice(tuple(all_first_names)).title()

        # surrogate = name_lookup[key.phi]
        
    elif val_type == 'last_name':
        # if key.phi not in name_lookup.keys():
        surrogate = random.choice(tuple(all_last_names)).title()

        # surrogate = name_lookup[key.phi]
    
    elif val_type == 'postal_code':
        surrogate = generate_postal_code()
    
    # Still need to figure out the best way to find the dates
    # case 'birth_date' | 'admission_date' | 'discharge_date':
    #     re.search(r'day|month|year', val, re.IGNORECASE)
    #     if isinstance(key.phi, Date):
    #         day, month, year = date_shifter(key.phi, day_shift, month_shift, year_shift)

    #         surrogate = build_date(day, month, year, month_before_day, year_first, month_name, month_abbr, suffix, leading_zeros)
    #     else:
    #         surrogate = '<PHI>'
    else:
        surrogate = '<PHI>'
    
    # indices = []
    increment = 0
    for m in re.finditer(r'\b' + re.escape(val) + r'\b', note, re.IGNORECASE):
        if m is not None:
            # print(note)
            # indices.append(tuple(m.start(),m.end()))
            deid_text = deid_text[:m.start()+increment] + surrogate + deid_text[m.end()+increment:]
            increment = increment + (len(surrogate) - len(val))
    # if found:
    #     for pair in indices:
    #         deid_text = deid_text[:m.start()] + surrogate + deid_text[m.end():]
    # if not found:
    #     deid_text = note
    # deid_text = note.replace(val, surrogate)
    return (surrogate, deid_text)