import re
import calendar
import random
import string
from ..phi_types.DateFinder import Date
from datetime import datetime

from faker import Faker
import ipdb


class PHIReplacer:
    """Handles replacement of PHI values with surrogate values."""

    def __init__(self, return_surrogates = False):


        self.return_surrogates = return_surrogates
        self.phis = {}
        self.note =''
        
        self.day_shift =None
        self.month_shift = None
        self.year_shift = None

        self.hour_shift = None
        self.minute_shift = None
        self.second_shift = None

        self.month_before_day = None
        self.year_first = None
        self.leading_zeros = None
        self.month_name = None

        self.suffix = None
        self.month_abbr = None

        self.name_lookup = None
        self.months = None
        self.days = None
        self.canadian_area_codes = None
        self.local_places_unambig = None

        self.custom_regexes = []

        self.fake = Faker()

    def set_note(self,new_note:str)-> None:
        self.note = new_note
  
    def set_phis(self,new_phis) -> None:
        self.phis = new_phis
        
    def load_phi_types(self, finder):
        self.months = finder.date_finder.months
        self.days = finder.date_finder.days
        self.canadian_area_codes = finder.contact_finder.canadian_area_codes
        self.local_places_unambig = finder.address_finder.local_places_unambig
        self.hospitals = finder.hospital_finder.hospitals
        self.hospital_acronyms = finder.hospital_finder.hospital_acronyms

    def replace_phi(self):
        """Replaces PHI in the text with surrogate values."""
        deid_text = ""
        surrogates = []
        where_we_left_off = 0

        self._randomize()

        for key in sorted(self.phis.keys(), key=lambda x: x.start):
            surrogate = self._get_surrogate(self.phis[key], key)
            surrogate_start = len(deid_text + self.note[where_we_left_off:key.start])
            deid_text = deid_text + self.note[where_we_left_off:key.start] + surrogate
            
            if self.return_surrogates:
                surrogate_end = surrogate_start + len(surrogate)
                surrogates.append({
                    'phi_start': key.start,
                    'phi_end': key.end,
                    'phi': key.phi,
                    'surrogate_start': surrogate_start,
                    'surrogate_end': surrogate_end,
                    'surrogate': surrogate,
                    'types': self.phis[key]
                })

            where_we_left_off = key.end

        deid_text = deid_text + self.note[where_we_left_off:]
     
        return (surrogates, deid_text)
    

    def _randomize(self):
        """ """

        # keep a consistent date shift so all dates maintain relative distace
        self.day_shift = random.randint(0, 29)
        self.month_shift = random.randint(0, 11)
        self.year_shift = random.randint(-30, 30)

        # similarly for time shift
        self.hour_shift = random.randint(0, 11)
        self.minute_shift = random.randint(0, 59)
        self.second_shift = random.randint(0, 59)

        # configure surrogate date format (will be consistent within note)
        self.month_before_day = random.choice([True, False])
        self.year_first = random.choice([True, False])
        self.leading_zeros = random.choice([True, False])
        self.month_name = random.choice([True, False])

        self.suffix = random.choice([True, False]) if self.month_name else False
        self.month_abbr = random.choice([True, False]) if self.month_name else False

        self.name_lookup = {}
        

    def _build_postal_code(self):
        """Generates a random postal code."""
        letters = random.choices(string.ascii_uppercase, k = 3)
        numbers = random.choices(string.digits, k = 3)

        res = ""

        for i in range(3):
            res = res + letters[i] + numbers[i]

        return res

    def _date_shifter(self, date):
        """Shifts a date by given day, month, and year offsets."""
        day = date.day
        month = date.month
        year = date.year

        res = ''

        if date.month is not None:
            old_month = self.months[month] if month in self.months else int(month)
            number_of_days = self.days[str(old_month)]

        if day is not None:
            day = int(day) + self.day_shift

            if old_month is not None:
                if int(day) > number_of_days:
                    old_month = int(old_month) + 1
                    day = int(day) % number_of_days
            else:
                day = int(day) % 31
        
        if month is not None:
            month = int(old_month) + self.month_shift

            if int(month) > 12:
                month = int(month) % 12
                if year is not None:
                    year = int(year) + 1
        
        if year is not None:
            year = int(year) + self.year_shift
            
        return day, month, year



    def _build_date(self, day, month, year):
        """Builds a formatted date string based on various configurations."""
        if month:
            if self.month_name and self.month_abbr:
                month = calendar.month_abbr[month]
            elif self.month_name and not self.month_abbr:
                month = calendar.month_name[month]
            else:
                month = str(month)

            if len(month) == 1 and self.leading_zeros:
                month = '0' + month
        
        if year:
            if year < 40: # add century if necessary
                year = str(year + 2000)
            elif year >= 40 and year < 1000:
                year = str(year + 1900)
            else:
                year = str(year)

        if day:
            if self.suffix:
                if 4 <= day <= 20 or 24 <= day <= 30:
                    day = str(day) + "th"
                else:
                    day = str(day) + ["st", "nd", "rd"][day % 10 - 1]
            else:
                day = str(day)

            if len(day) == 1 and self.leading_zeros:
                day = '0' + day
        
        res = ''
        
        if not self.suffix:
            if self.month_name:
                sep = random.choice(['-', ' '])
            else:
                sep = random.choice(['-', ' ', '/'])
                
            if day and month and self.month_before_day:
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

                if self.year_first:
                    res = year + year_sep + res
                else:
                    res = res + year_sep + year
                
        if self.suffix: # month_name must be true
                
            if day and month and self.month_before_day:
                res = day + ' of ' + month
                
                if year:
                    year_sep = random.choice(['. ', ', ', ' '])
                    res = res + year_sep + year
        
            elif day and year and (not month):
                res = day + ' of ' + year
                
            else:
                sep = random.choice(['-', ' '])
                
                if day and month and (not self.month_before_day):
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

                    if self.year_first:
                        res = year + year_sep + res
                    else:
                        res = res + year_sep + year

        return res

    def _time_shifter(self, time):
        """Shifts a time by given hour, minute, and second offsets."""
        hours = time.hours
        minutes = time.minutes
        seconds = time.seconds
        meridiem = time.meridiem

        if seconds is not None: # seconds is optional as per the regex
            seconds = int(seconds) + self.second_shift

            if int(seconds) > 60 and minutes is not None:
                seconds = int(seconds) % 60
                minutes = int(minutes) + 1
        else:
            seconds = "00"
        
        if minutes is not None:
            minutes = int(minutes) + self.minute_shift

            if int(minutes) > 60 and hours is not None:
                minutes = int(minutes) % 60
                hours = int(hours) + 1
        else:
            minutes = "00"

        if hours is not None:
            hours = int(hours) + self.hour_shift
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

    def _build_telephone(self):
        """Generates a random telephone number."""
        return random.choice(tuple(self.canadian_area_codes)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(1000, 9999))

    def _build_ohip(self):
        """Generates a random OHIP number."""
        return str(random.randint(1000, 9999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))

    def _build_sin(self):
        """Generates a random SIN number."""
        return str(random.randint(100, 999)) + '-' + str(random.randint(100, 999)) + '-' + str(random.randint(100, 999))
    
    def _build_id(self):
        return random.randint(10000000, 99999999)

    def _get_surrogate(self, phi_values, key):
        """Determines the surrogate value for a given PHI type."""
      
        surrogate = ''
        print(phi_values)
        
        for val in phi_values:
            if re.search(r'Initials \(double\)', val, re.IGNORECASE):
                surrogate =  f"{random.choice(string.ascii_uppercase)}.{random.choice(string.ascii_uppercase)}."
                while surrogate == key.phi:
                    surrogate =  f"{random.choice(string.ascii_uppercase)}.{random.choice(string.ascii_uppercase)}."

            elif re.search(r'Initials \(single\)',val,re.IGNORECASE):
                
                surrogate = f"{random.choice(string.ascii_uppercase)}."
                while surrogate == key.phi:
                    surrogate = f"{random.choice(string.ascii_uppercase)}."

            elif re.search('MRN', val, re.IGNORECASE) :
                surrogate= str(random.randint(0, 10**7))

            elif re.search('SIN', val, re.IGNORECASE):
                surrogate= self._build_sin()

            elif re.search('OHIP', val, re.IGNORECASE):
                surrogate= self._build_ohip()

            elif re.search('Telephone/Fax', val):
                surrogate= self._build_telephone()

            elif re.search('Email Address', val):
                surrogate= self.fake.company_email()

            elif re.search('Address', val):
                surrogate= self.fake.street_address()

            elif re.search('Location', val):
                surrogate= random.choice(tuple(self.local_places_unambig))

            elif re.search('(First Name)|(first_name \(MLL\))', val):
                if key.phi not in self.name_lookup:
                    self.name_lookup[key.phi] = self.fake.first_name()
                surrogate= self.name_lookup[key.phi]

            elif re.search('(Last Name)|(last_name \(MLL\))', val):
                if key.phi not in self.name_lookup:
                    self.name_lookup[key.phi] = self.fake.last_name()
                surrogate= self.name_lookup[key.phi]

            elif re.search('Name Prefix', val):
                surrogate= ""

            elif re.search('Name', val):
                if key.phi not in self.name_lookup:
                    self.name_lookup[key.phi] = self.fake.first_name()
                surrogate= self.name_lookup[key.phi]
        

            elif re.search('(Postalcode)|(postal_code \(MLL\))', val):
                surrogate= self._build_postal_code()
            
            elif re.search(r'date|day|month|year|(_date \(MLL\))', val, re.IGNORECASE):
                if isinstance(key.phi, Date):
                    day, month, year = self._date_shifter(key.phi)
                    surrogate= self._build_date(day, month, year)
                elif re.search(r'Date range',val,re.IGNORECASE):
                    surrogate+= self.fake.date()+ " to " + self.fake.future_date().strftime('%Y-%m-%d')
                    
                else:
                    surrogate= self.fake.date()

            elif re.search('Time', val, re.IGNORECASE):
                surrogate = self._time_shifter(key.phi)

            elif re.search('Holiday', val):
                surrogate = ""

            elif re.search('_id (MLL)', val):
                surrogate = self._build_id()
            
            elif re.search('Hospital', val):
                surrogate = random.choice(self.hospitals).title()

            elif re.search('Site Acronym', val, re.IGNORECASE):
                surrogate = random.choice(self.hospital_acronyms)

            elif self.custom_regexes:

                for custom_regex in self.custom_regexes:
                    if val == custom_regex.phi_type:
                        surrogate = custom_regex.surrogate_builder_fn(*custom_regex.arguments)

            else:
                surrogate = '<PHI>'
            
            if surrogate != '<PHI>': # for multiple PHI types for a single token, just pick one
                break

        # if surrogate == '<PHI>': # in the case, phitypes has only types giving <PHI> surrogates
        #     surrogate = ''

        return surrogate
        