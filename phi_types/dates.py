import re
from collections import namedtuple
from this import d
from phi_types.utils import add_type, PHI, is_probably_measurement


two_digit_threshold = 30
valid_year_low = 1900
valid_year_high = 2050

Date = namedtuple("Date", ["date_string", "day", "month", "year"])
Time = namedtuple("Time", ["time_string", "hours", "minutes", "seconds", "meridiem"])


months = {
    "January":1, "Jan":1, 
    "February":2, "Feb":2, 
    "March":3, "Mar":3, 
    "April":4, "Apr":4, 
    "May":5, 
    "June":6, "Jun":6, 
    "July":7, "Jul":7, 
    "August":8, "Aug":8, 
    "September":9, "Sept":9, "Sep":9, 
    "October":10, "Oct":10, 
    "November":11, "Nov":11, 
    "December":12, "Dec":12
    }


days = {"1":31, "2":28, "3":31, "4":30, "5":31, "6":30, "7":31, "8":31, "9":30, "10":31, "11":30, "12":31}


def is_valid_date(date):
    if date.year is not None:
        try: # safe type-casting
            year = int(year)
        except:
            return False

        if len(date.year) == 2:
            
            if year < two_digit_threshold:
                year = 2000 + year
            else:
                year = 1900 + year
        else:
            year = date.year
            
        if not is_valid_year(year):
            return False
    
    if date.month is not None and date.day is not None:
        try:
            if date.month in months:
                month = months[date.month]
            else:
                month = int(date.month)
            day = int(date.day)
        except:
            return False

        # month and days are switched
        if month < 1 or month > 12 or day < 1 or day > 31:
            if day >= 1 and day <= 12 and month >= 1 and month <= 31:
                actually_month = day
                day = month
                month = actually_month
            else:
                return False
    
        # check validity of February days
        if month == 2:
            if ((date.year is not None) and ((year % 4) == 0) and (year != 2000)):
                return day <= 29
            else:
                return day <= 28
        elif ((month == 4) or (month == 6) or (month == 9) or (month == 11)):
            return day <= 30
        
        return day <= 31 


def is_valid_year(year):
    if isinstance(year, str):
        try:
            year = int(year)
        except:
            return False

    if isinstance(year, int):
        return (year >= valid_year_low) and (year <= valid_year_high)


def is_valid_day(day):
    if isinstance(day, str):
        try:
            day = int(day)
        except:
            return False

    if isinstance(day, int):
        return (day < 32) and (day > 0)


def is_valid_month(month):
    if isinstance(month, str):
        if month in months:
            month = months[month]
        else:
            try:
                month = int(month)
            except:
                return False

    if isinstance(month, int):
        return (month <= 12) and (month > 0)


def is_valid_time(time, military=False):
    if time.hours is not None:
        try:
            hours = int(time.hours)
        except:
            return False

    if time.minutes is not None:
        try:
            minutes = int(time.minutes)
        except:
            return False

    if  hours > 0 and ((hours <= 12) or (military and hours < 24)) and minutes >= 0 and minutes < 60:
        if time.seconds is not None:
            try:
                seconds = int(time.seconds)
            except:
                return False

            return seconds >= 0 and seconds < 60
        else:
            return True

    return False


def is_probably_date(string_before, string_after):
    if (
        not is_probably_measurement(string_before) and 
        not re.search(r'\b(drop|up|cc|dose|doses|range|ranged|pad|rate|bipap|pap|unload|ventilation|scale|cultures|blood|at|up|with|in|of|RR|ICP|CVP|strength|PSV|SVP|PCWP|PCW|BILAT|SRR|VENT|PEEP\/PS|flowby|drinks|stage) ?', string_before, re.IGNORECASE) and
        not re.search(r' ?(packs|litres|puffs|mls|liters|L|pts|patients|range|psv|scale|beers|per|esophagus|tabs|tablets|systolic|sem|strength|hours|pts|times|drop|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|hr|hrs|hour|hours|bottles|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns|units|amp|qd|chest pain|intensity)\b', string_after, re.IGNORECASE)
    ):
        return True
    return False


def holiday(x, phi):
    for m in re.finditer(r'\bchristmas|thanksgiving|easter|hanukkah|rosh hashanah|ramadan|victoria day|canada day|labour day\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'Holiday', phi)


def date(x, phi):
    # mm/dd-mm/dd
    for m in re.finditer(r'\b((\d\d?)\/(\d\d?)\-(\d\d?)\/(\d\d?))\b', x):
        date_1 = x[m.start(2):m.end(3)]
        date_1_key = Date(date_1, m.group(3), m.group(2), None)

        date_2 = x[m.start(4):m.end(5)]
        date_2_key = Date(date_2, m.group(5), m.group(4), None)

        if is_valid_date(date_1_key) and is_valid_date(date_2_key):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (1)', phi)
            
    # mm/dd/yy-mm/dd/yy or mm/dd/yyyy-mm/dd/yyyy
    for m in re.finditer(r'\b((\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b', x):
        date_1 = x[m.start(2):m.end(4)]
        date_1_key = Date(date_1, m.group(3), m.group(2), m.group(4))

        date_2 = x[m.start(5):m.end(7)]
        date_2_key = Date(date_2, m.group(6), m.group(5), m.group(7))

        if is_valid_date(date_1_key) and is_valid_date(date_2_key):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (2)', phi)
            
    # mm/dd-mm/dd/yy or mm/dd-mm/dd/yyyy
    for m in re.finditer(r'\b((\d\d?)\/(\d\d?)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b', x):
        date_1 = x[m.start(2):m.end(4)]
        date_1_key = Date(date_1, m.group(3), m.group(2), None)

        date_2 = x[m.start(5):m.end(7)]
        date_2_key = Date(date_2, m.group(5), m.group(4), m.group(6))

        if is_valid_date(date_1_key) and is_valid_date(date_2_key):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (3)', phi)
            
    # month/day/year
    for m in re.finditer(r'\b(\d\d?)[\-\/\.](\d\d?)[\-\/\.](\d\d|\d{4})\b', x):
        start = m.start()
        end = m.end()
        
        month = m.group(1)
        day = m.group(2)
        year = m.group(3)
        
        date_key = Date(m.group(), day, month, year)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\%\/]', string_after) or re.search(r'\S\d', string_after)):
                if is_valid_date(date_key):
                    add_type(PHI(start, end, date_key), 'Month/Day/Year', phi)
            
    # day/month/year
    for m in re.finditer(r'\b(\d\d?)[\-\/](\d\d?)[\-\/](\d\d|\d{4})\b', x):
        start = m.start()
        end = m.end()

        day = m.group(1)
        month = m.group(2)
        year = m.group(3)

        date_key = Date(m.group(), day, month, year)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\%\/]', string_after) or re.search(r'\S\d', string_after)):
            if is_valid_date(date_key):
                add_type(PHI(start, end, date_key), 'Month/Day/Year', phi)
            
    # year/month/day
    for m in re.finditer(r'\b(\d\d|\d{4})[\-\/\.](\d\d?)[\-\/\.](\d\d?)\b', x):
        start = m.start()
        end = m.end()

        year = m.group(1)
        month = m.group(2)
        day = m.group(3)

        date_key = Date(m.group(), day, month, year)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after) or (re.search(r'\S\d', string_after))):
            if is_valid_date(date_key) and ((int(year) > 50) or (int(year) < 6)):
                prev_chars = x[(start - 4):start]
                next_chars = x[end:(end + 11)]

                if re.search(r'(\d)(\s)?(\|)(\s)?', prev_chars) and re.search(r'\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)', next_chars):
                    add_type(PHI(start, end, date_key), 'Header Date', phi)
                else:
                    add_type(PHI(start, end, date_key), 'Year/Month/Day', phi)
                    
    # year/day/month
    for m in re.finditer(r'\b(\d\d|\d{4})[\-\/](\d\d?)[\-\/](\d\d?)\b', x):
        start = m.start()
        end = m.end()

        year = m.group(1)
        day = m.group(2)
        month = m.group(3)

        date_key = Date(m.group(), day, month, year)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after) or (re.search(r'\S\d', string_after))):
            if is_valid_date(date_key) and ((int(year) > 50) or (int(year) < 6)):
                prev_chars = x[(start - 4):start]
                next_chars = x[end:(end + 11)]

                if re.search(r'(\d)(\s)?(\|)(\s)?', prev_chars) and re.search(r'\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)', next_chars):
                    add_type(PHI(start, end, date_key), 'Header Date', phi)
                else:
                    add_type(PHI(start, end, date_key), 'Year/Month/Day', phi)
                    
    # mm/yyyy
    for m in re.finditer(r'\b((\d\d?)[\-\/](\d{4}))', x):
        start = m.start()
        end = m.end()

        month = m.group(2)
        year = m.group(3)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\/\.\%]', string_after)):
                
                if is_valid_month(month) and is_valid_year(year):
                    date_key = Date(m.group(), None, month, year)
                    add_type(PHI(start, end, date_key), 'Month/Year 1', phi)
                    
    # yyyy/mm
    for m in re.finditer(r'\b((\d{4})[\-\/](\d\d?))\b', x):
        start = m.start()
        end = m.end()

        year = m.group(2)
        month = m.group(3)

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\/\.\%]', string_after)):
                
                if is_valid_month(month) and is_valid_year(year):
                    date_key = Date(m.group(), None, month, year)
                    add_type(PHI(start, end, date_key), 'Month/Year 1', phi)
                    
    for month in months:
        
        # 2-May-04
        for m in re.finditer(r'\b((\d{1,2})[ \-]?' + month + r'[ \-\,]? ?\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = m.group(2)
            year = m.group(3)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, year)
                add_type(PHI(m.start(), m.end(), date_key), 'Day Month Year', phi)
        
        # 1 through 2-May-04
        for m in re.finditer(r'\b((\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[ \-]?' + month + r'[ \-\,]? ?\'?\d{2,4})\b', x, re.IGNORECASE):
            day1 = m.group(2)
            day2 = m.group(4)
                    
            if is_valid_day(day1) and is_valid_day(day2):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (4)', phi)

        # Apr. 2 05            
        for m in re.finditer(r'\b(' + month + r'\b\.? (\d{1,2})[\,\s]+ *\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = m.group(2)
            year = m.group(3)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, year)
                add_type(PHI(m.start(), m.end(), date_key), 'Month Day Year', phi)
        
        # Mar 1 to 2 05
        for m in re.finditer(r'\b(' + month + r'\b\.? (\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[\,\s]+ *\'?\d{2,4})\b', x, re.IGNORECASE):
            day1 = m.group(2)
            day2 = m.group(4)
                    
            if is_valid_day(day1) and is_valid_day(day2):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (4)', phi)
        
        # Apr. 12th 2000
        for m in re.finditer(r'\b(' + month + r'\b\.?,? ?(\d{1,2})(|st|nd|rd|th|) ?[\,\s]+ *\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = m.group(2)
            year = m.group(4)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, year)
                add_type(PHI(m.start(), m.end(), date_key), 'Month Day Year (2)', phi)
                    
        # Apr. 12th
        for m in re.finditer(r'\b(' + month + r'\b\.?,?\s*(\d{1,2})(|st|nd|rd|th|)?)\b', x, re.IGNORECASE):
            day = m.group(2)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, None)
                add_type(PHI(m.start(), m.end(), date_key), 'Month Day', phi)
                    
        # Apr. 12 -> 22nd
        for m in re.finditer(r'\b(' + month + r'\b\.?,? ?(\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?)\b', x, re.IGNORECASE):
            day1 = m.group(2)
            day2 = m.group(4)

            if is_valid_day(day1) and is_valid_day(day2):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (6)', phi)
                    
        # 12th of April
        for m in re.finditer(r'\b((\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b' + month + r')\b', x, re.IGNORECASE):
            day = m.group(2)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, None)
                add_type(PHI(m.start(), m.end(), date_key), 'Day Month', phi)
                    
        # 12th of April. 2005
        for m in re.finditer(r'\b(((\d{1,2})(|st|nd|rd|th|)?\s+(of\s)?[\-]?\b(' + month + r')\.?,?)\s+(\d{2,4}))\b', x, re.IGNORECASE):
            day = m.group(3)
            year = m.group(7)
                    
            if is_valid_day(day):
                date_key = Date(m.group(), day, month, year)
                add_type(PHI(m.start(), m.end(), date_key), 'Day Month Year (2)', phi)
                    
        # 12th - 2nd of Apr
        for m in re.finditer(r'\b((\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b' + month + r')\b', x, re.IGNORECASE):
            day1 = m.group(2)
            day2 = m.group(5)
                    
            if is_valid_day(day1) and is_valid_day(day2):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (7)', phi)

        # Apr. of 2002
        for m in re.finditer(r'\b(' + month + r'\.?,? ?(of )?(\d{2}\d{2}?))\b', x, re.IGNORECASE):
            year = m.group(3)
            date_key = Date(m.group(), None, month, year)
            
            add_type(PHI(m.start(), m.end(), date_key), 'Month Year', phi)


def date_with_context_check(x, phi):
    # mm/dd or mm/yy
    for m in re.finditer(r'\b([A-Za-z0-9%\/]+ +)?((\d\d?)([\/\-])(\d\d?))\/?\/?( +[A-Za-z]+)?\b', x):
        month = m.group(3)
        day_or_year = m.group(5)

        if (
            (m.group(1) is None or not re.search(r'\b(cvp|noc|\%|RR|PCW)', m.group(1), re.IGNORECASE)) and
            (m.group(6) is None or not re.search(r'\bpersantine\b', m.group(6), re.IGNORECASE))
        ):
            context_len = 12
            chars_before = x[(m.start(3) - 2):m.start(3)]
            chars_after = x[m.end(5):(m.end(5) + 2)]

            if not re.search(r'\d[\/\.\-]', chars_before) and not re.search(r'[\%]', chars_after) and not re.search(r'\S\d', chars_after):
                string_before = x[(m.start(3) - context_len):m.start(3)]
                string_after = x[m.end(5):(m.end(5) + context_len)]
                date_key_mm_dd = Date(m.group(2), day_or_year, month, None)

                if is_valid_date(date_key_mm_dd):

                    if int(day_or_year) == 5:
                        if (
                            not is_probably_measurement(string_before) and 
                            not re.search(r'\bPSV? ', string_before, re.IGNORECASE) and 
                            not re.search(r'\b(CPAP|PS|range|bipap|pap|pad|rate|unload|ventilation|scale|strength|drop|up|cc|rr|cvp|at|up|in|with|ICP|PSV|of) ', string_before, re.IGNORECASE) and
                            not (r' ?(packs|psv|puffs|pts|patients|range|scale|mls|liters|litres|drinks|beers|per|esophagus|tabs|pts|tablets|systolic|sem|strength|times|bottles|drop|drops|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|L|hr|hrs|hour|hours|dose|doses|cultures|blood|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', string_after, re.IGNORECASE)
                        ):
                            add_type(PHI(m.start(3), m.end(5), date_key_mm_dd), 'Month/Day (1)', phi)

                    elif int(day_or_year) == 2:
                        if (
                            not is_probably_measurement(string_before) and 
                            not re.search(r' ?hour\b', string_after, re.IGNORECASE) and 
                            not re.search(r'\b(with|drop|bipap|pap|range|pad|rate|unload|ventilation|scale|strength|up|cc|rr|cvp|at|up|with|in|ICP|PSV|of) ', string_before, re.IGNORECASE) and 
                            not re.search(r' ?hr\b', string_after, re.IGNORECASE) and 
                            not (r' ?(packs|L|psv|puffs|pts|patients|range|scale|dose|doses|cultures|blood|mls|liters|litres|pts|drinks|beers|per|esophagus|tabs|tablets|systolic|sem|strength|bottles|times|drop|cc|up|mg|\/hr|\/hour|mcg|ug|mm|PEEP|hr|hrs|hour|hours|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', string_after, re.IGNORECASE)
                        ):
                            add_type(PHI(m.start(3), m.end(5), date_key_mm_dd), 'Month/Day (2)', phi)
                    
                    else:
                        if is_probably_date(string_before, string_after):
                            add_type(PHI(m.start(3), m.end(5), date_key_mm_dd), 'Month/Day (3)', phi)

                if (
                    is_valid_month(month) and len(day_or_year) == 2 and 
                    ((int(day_or_year) >= 50) or (int(day_or_year) <= 30))
                ):
                    if is_probably_date(string_before, string_after):
                        date_key_mm_yy = Date(m.group(2), None, month, day_or_year)
                        add_type(PHI(m.start(3), m.end(5), date_key_mm_yy), 'Month/Year (2)', phi)


def year_with_context_check(x, phi):
    # YEAR_INDICATOR + yy
    for m in re.finditer(r'\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|avr|x2|x3|CHOLECYSTECTOMY|cva|ca|PTC|PTCA|stent|since|surgery|year) + *(\')?)(\d\d)(\.\d)?((\.|\:)\d{1,2})?\b', x, re.IGNORECASE):
        
        if m.group(5) is None and m.group(6) is None: # avoid decimal places or hh:mm
            date_key = Date(m.group(4), None, None, m.group(4))
            add_type(PHI(m.start(4), m.end(4), date_key), 'Year (2 digits)', phi)

    for m in re.finditer(r'\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|x2|x3|CHOLECYSTECTOMY|cva|ca|in|PTCA|since|from|year) + *)(\d{4})((\,? )\d{4})?\b', x, re.IGNORECASE):
        year_1 = m.group(3)

        if is_valid_year(year_1):
            add_type(PHI(m.start(3), m.end(3), Date(m.group(3), None, None, year_1)), 'Year (4 digits)', phi)

            if m.group(4) is not None:
                year_2 = m.group(4)
                add_type(PHI(m.start(4), m.end(4), Date(m.group(4), None, None, year_2)), 'Year (4 digits)', phi)


def season_year(x, phi):
    seasons = ["winter", "spring", "summer", "autumn", "fall"]

    for season in seasons:
        for m in re.finditer(r'\b((' + season + r')(( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b', x, re.IGNORECASE):
            year = m.group(7)
            date_key = Date(m.group(7), None, None, year)

            if len(year) == 4 and is_valid_year(year):
                add_type(PHI(m.start(7), m.end(7), date_key), 'Year (4 digits)', phi)
            else:
                add_type(PHI(m.start(7), m.end(7), date_key), 'Year (2 digits)', phi)


def find_time(x, phi):
    for m in re.finditer(r'\b( *)((\d{4}) *)(hours|hr|hrs|h)\b', x, re.IGNORECASE):
        potential_time = m.group(3)

        if int(potential_time) < 2359 and int(potential_time) >= 0:
            hours = int(potential_time) // 100
            minutes = int(potential_time) % 100
            time_key = Time(m.group(3), hours, minutes, None, None)

            add_type(PHI(m.start(3), m.end(3), time_key), 'Time (military)', phi)

    for m in re.finditer(r'(([A-Za-z0-9%\/]+)\s[A-Za-z0-9%\/]+\s+)?((\d\d?)\:(\d{2})(\:(\d\d))?)(\s)?(am|pm|p.m.|a.m.)?( *([A-Za-z]+))?', x, re.IGNORECASE):
        
        pre = m.group(1)
        post = m.group(11)

        hours = m.group(4)
        minutes = m.group(5)
        seconds = m.group(6)

        meridiem = m.group(9)

        time_key = Time(m.group(3), hours, minutes, seconds, meridiem)

        if meridiem is not None:
            if is_valid_time(time_key):
                add_type(PHI(m.start(3), m.end(3), time_key), 'Time', phi)

        elif (
            is_valid_time(time_key, military=True) and (
            pre is None or (
                not is_probably_measurement(pre) and 
                not re.search(r'\bPSV? ', pre, re.IGNORECASE) and 
                not re.search(r'\b(CPAP|PS|range|bipap|pap|pad|rate|unload|ventilation|scale|strength|drop|up|cc|rr|cvp|at|up|in|with|ICP|PSV|of) ', pre, re.IGNORECASE)
                )
            ) and (
            post is None or (
                not re.search(r' ?(packs|psv|puffs|pts|patients|range|scale|mls|liters|litres|drinks|beers|per|esophagus|tabs|pts|tablets|systolic|sem|strength|times|bottles|drop|drops|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|L|hr|hrs|hour|hours|dose|doses|cultures|blood|bpm|ICP|CPAP|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', post, re.IGNORECASE)
                )
            )
        ):
            add_type(PHI(m.start(3), m.end(3), time_key), 'Time', phi)


def monthly(x, phi):
    for m in re.finditer(r'\b(every )((\d|\d{2})(nd|st|th|rd)?(( month)?( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b', x, re.IGNORECASE):
        year = m.group(10)
        date_key = Date(m.group(10), None, None, year)

        if len(year) == 4:
            if is_valid_year(year):
                add_type(PHI(m.start(10), m.end(10), date_key), 'Year (Monthly 4 digit)', phi)

        else:
            add_type(PHI(m.start(10), m.end(10), date_key), 'Year (Monthly 2 digit)', phi)