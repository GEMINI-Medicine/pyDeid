import re
from collections import namedtuple
from phi_types.utils import add_type, PHI, is_probably_measurement


two_digit_threshold = 30
valid_year_low = 1900
valid_year_high = 2050

Date = namedtuple("Date", ["date_string", "day", "month", "year"])
Time = namedtuple("Time", ["time_string", "hours", "minutes", "seconds"])


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


def is_valid_date(month, day, year):
    if year != -1 and len(str(year)) == 2:
        if year < two_digit_threshold:
            year = '20' + year
        else:
            year = '19' + year
            
    if year != -1 and ((year < valid_year_low) or (year > valid_year_high)):
        return False
    
    # invalid month and days
    if month < 1 or month > 12 or day < 1 or day > 31:
        if day >= 1 and day <= 12 and month >= 1 and month <= 31:
            tmpday = day
            day = month
            month = tmpday
        else:
            return False
    
    # check validity of February days
    if month == 2:
        if ((year != -1) and ((year % 4) == 0) and (year != 2000)):
            return day <= 29
        else:
            return day <= 28
    elif ((month == 4) or (month == 6) or (month == 9) or (month == 11)):
        return day <= 30
    
    return day <= 31 


def is_valid_time(hours, minutes, seconds):
    if  hours > 0 and hours <= 12 and minutes >= 0 and minutes < 60:
        if seconds is not None:
            return seconds >= 0 and seconds < 60

    return False


def is_valid_24_hour_time(hours, minutes, seconds):
    if  hours > 0 and hours <= 24 and minutes >= 0 and minutes < 60:
        if seconds is not None:
            return seconds >= 0 and seconds < 60

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
        
        if is_valid_date(m.group(2), m.group(3), -1) and is_valid_date(m.group(4), m.group(5), -1):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (1)', phi)
            
    # mm/dd/yy-mm/dd/yy or mm/dd/yyyy-mm/dd/yyyy
    for m in re.finditer(r'\b((\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b', x):
        
        if is_valid_date(m.group(2), m.group(3), m.group(4)) and is_valid_date(m.group(5), m.group(6), m.group(7)):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (2)', phi)
            
    # mm/dd-mm/dd/yy or mm/dd-mm/dd/yyyy
    for m in re.finditer(r'\b((\d\d?)\/(\d\d?)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b', x):
        
        if is_valid_date(m.group(6), m.group(2), m.group(3)) and is_valid_date(m.group(6), m.group(4), m.group(5)):
            add_type(PHI(m.start(), m.end(), m.group()), 'Date range (3)', phi)
            
    # month/day/year
    for m in re.finditer(r'\b(\d\d?)[\-\/\.](\d\d?)[\-\/\.](\d\d|\d{4})\b', x):
        start = m.start()
        end = m.end()
        
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\%\/]', string_after) or re.search(r'\S\d', string_after)):
                if is_valid_date(month, day, year):
                    add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Month/Day/Year', phi)
            
    # day/month/year
    for m in re.finditer(r'\b(\d\d?)[\-\/](\d\d?)[\-\/](\d\d|\d{4})\b', x):
        start = m.start()
        end = m.end()

        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\%\/]', string_after) or re.search(r'\S\d', string_after)):
            if is_valid_date(month, day, year):
                add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Month/Day/Year', phi)
            
    # year/month/day
    for m in re.finditer(r'\b(\d\d|\d{4})[\-\/\.](\d\d?)[\-\/\.](\d\d?)\b', x):
        start = m.start()
        end = m.end()

        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after) or (re.search(r'\S\d', string_after))):
            if is_valid_date(month, day, year) and ((year > 50) or (year < 6)):
                prev_chars = x[(start - 4):start]
                next_chars = x[end:(end + 11)]

                if re.search(r'(\d)(\s)?(\|)(\s)?', prev_chars) and re.search(r'\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)', next_chars):
                    add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Header Date', phi)
                else:
                    add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Year/Month/Day', phi)
                    
    # year/day/month
    for m in re.finditer(r'\b(\d\d|\d{4})[\-\/](\d\d?)[\-\/](\d\d?)\b', x):
        start = m.start()
        end = m.end()

        year = int(m.group(1))
        day = int(m.group(2))
        month = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after) or (re.search(r'\S\d', string_after))):
            if is_valid_date(month, day, year) and ((year > 50) or (year < 6)):
                prev_chars = x[(start - 4):start]
                next_chars = x[end:(end + 11)]

                if re.search(r'(\d)(\s)?(\|)(\s)?', prev_chars) and re.search(r'\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)', next_chars):
                    add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Header Date', phi)
                else:
                    add_type(PHI(start, end, Date(m.group(), day, month, year)), 'Year/Month/Day', phi)
                    
    # mm/yyyy
    for m in re.finditer(r'\b((\d\d?)[\-\/](\d{4}))', x):
        start = m.start()
        end = m.end()

        month = int(m.group(2))
        year = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\/\.\%]', string_after)):
                
                if (month <= 12) and (month > 0) and (year >= valid_year_low) and (year <= valid_year_high):
                    add_type(PHI(start, end, Date(m.group(), None, month, year)), 'Month/Year 1', phi)
                    
    # yyyy/mm
    for m in re.finditer(r'\b((\d{4})[\-\/](\d\d?))\b', x):
        start = m.start()
        end = m.end()

        year = int(m.group(2))
        month = int(m.group(3))

        string_before = x[(start - 2):start]
        string_after = x[end:(end + 2)]

        if not (re.search(r'(\|\|)', string_before) or re.search(r'(\|\|)', string_after)):
            
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'[\/\.\%]', string_after)):
                
                if (month <= 12) and (month > 0) and (year >= valid_year_low) and (year <= valid_year_high):
                    add_type(PHI(start, end, Date(m.group(), None, month, year)), 'Month/Year 1', phi)
                    
    for month in months:
        
        # 2-May-04
        for m in re.finditer(r'\b((\d{1,2})[ \-]?' + month + r'[ \-\,]? ?\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = int(m.group(2))
            year = int(m.group(3))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, year)), 'Day Month Year', phi)
        
        # 1 through 2-May-04
        for m in re.finditer(r'\b((\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[ \-]?' + month + r'[ \-\,]? ?\'?\d{2,4})\b', x, re.IGNORECASE):
            day1 = int(m.group(2))
            day2 = int(m.group(4))
                    
            if (day1 < 32) and (day1 > 0) and (day2 < 32) and (day2 > 0):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (4)', phi)

        # Apr. 2 05            
        for m in re.finditer(r'\b(' + month + r'\b\.? (\d{1,2})[\,\s]+ *\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = int(m.group(2))
            year = int(m.group(3))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, year)), 'Month Day Year', phi)
        
        # Mar 1 to Apr. 2 05
        for m in re.finditer(r'\b(' + month + r'\b\.? (\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[\,\s]+ *\'?\d{2,4})\b', x, re.IGNORECASE):
            day1 = int(m.group(2))
            day2 = int(m.group(4))
                    
            if (day1 < 32) and (day1 > 0) and (day2 < 32) and (day2 > 0):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (4)', phi)
        
        # Apr. 12th 2000
        for m in re.finditer(r'\b(' + month + r'\b\.?,? ?(\d{1,2})(|st|nd|rd|th|) ?[\,\s]+ *\'?(\d{2,4}))\b', x, re.IGNORECASE):
            day = int(m.group(2))
            year = int(m.group(4))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, year)), 'Month Day Year (2)', phi)
                    
        # Apr. 12th
        for m in re.finditer(r'\b(' + month + r'\b\.?,?\s*(\d{1,2})(|st|nd|rd|th|)?)\b', x, re.IGNORECASE):
            day = int(m.group(2))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, None)), 'Month Day', phi)
                    
        # Apr. 12 -> 22nd
        for m in re.finditer(r'\b(' + month + r'\b\.?,? ?(\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?)\b', x, re.IGNORECASE):
            day1 = int(m.group(2))
            day2 = int(m.group(4))
                    
            if (day1 < 32) and (day1 > 0) and (day2 < 32) and (day2 > 0):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (6)', phi)
                    
        # 12th of April
        for m in re.finditer(r'\b((\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b' + month + r')\b', x, re.IGNORECASE):
            day = int(m.group(2))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, None)), 'Day Month', phi)
                    
        # 12th of April. 2005
        for m in re.finditer(r'\b(((\d{1,2})(|st|nd|rd|th|)?\s+(of\s)?[\-]?\b(' + month + r')\.?,?)\s+(\d{2,4}))\b', x, re.IGNORECASE):
            day = int(m.group(3))
            year = int(m.group(7))
                    
            if (day < 32) and (day > 0):
                add_type(PHI(m.start(), m.end(), Date(m.group(), day, month, year)), 'Day Month Year (2)', phi)
                    
        # 12th - 2nd of Apr
        for m in re.finditer(r'\b((\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b' + month + r')\b', x, re.IGNORECASE):
            day1 = int(m.group(2))
            day2 = int(m.group(5))
                    
            if (day1 < 32) and (day1 > 0) and (day2 < 32) and (day2 > 0):
                add_type(PHI(m.start(), m.end(), m.group()), 'Date range (7)', phi)

        # Apr. of 2002
        for m in re.finditer(r'\b(' + month + r'\.?,? ?(of )?(\d{2}\d{2}?))\b', x, re.IGNORECASE):
            year = int(m.group(3))
            
            add_type(PHI(m.start(), m.end(), Date(m.group(), None, month, year)), 'Month Year', phi)


def date_with_context_check(x, phi):
    # mm/dd or mm/yy
    for m in re.finditer(r'\b([A-Za-z0-9%\/]+ +)?((\d\d?)([\/\-])(\d\d?))\/?\/?( +[A-Za-z]+)?\b', x):
        month = int(m.group(3))
        day_or_year = int(m.group(5))

        if not re.search(r'\b(cvp|noc|\%|RR|PCW)', m.group(1), re.IGNORECASE) and not re.search(r'\bpersantine\b', m.group(6), re.IGNORECASE):
            context_len = 12
            chars_before = x[(m.start(3) - 2):m.start(3)]
            chars_after = x[m.end(5):(m.end(5) + 2)]

            if not re.search(r'\d[\/\.\-]', chars_before) and not re.search(r'[\%]', chars_after) and not re.search(r'\S\d', chars_after):
                string_before = x[(m.start(3) - context_len):m.start(3)]
                string_after = x[m.end(5):(m.end(5) + context_len)]
                
                if is_valid_date(month, day_or_year, -1):

                    if day_or_year == 5:
                        if (
                            not is_probably_measurement(string_before) and 
                            not re.search(r'\bPSV? ', string_before, re.IGNORECASE) and 
                            not re.search(r'\b(CPAP|PS|range|bipap|pap|pad|rate|unload|ventilation|scale|strength|drop|up|cc|rr|cvp|at|up|in|with|ICP|PSV|of) ', string_before, re.IGNORECASE) and
                            not (r' ?(packs|psv|puffs|pts|patients|range|scale|mls|liters|litres|drinks|beers|per|esophagus|tabs|pts|tablets|systolic|sem|strength|times|bottles|drop|drops|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|L|hr|hrs|hour|hours|dose|doses|cultures|blood|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', string_after, re.IGNORECASE)
                        ):
                            add_type(PHI(m.start(3), m.end(5), Date(m.group(2), day_or_year, month, None)), 'Month/Day (1)', phi)

                    elif day_or_year == 2:
                        if (
                            not is_probably_measurement(string_before) and 
                            not re.search(r' ?hour\b', string_after, re.IGNORECASE) and 
                            not re.search(r'\b(with|drop|bipap|pap|range|pad|rate|unload|ventilation|scale|strength|up|cc|rr|cvp|at|up|with|in|ICP|PSV|of) ', string_before, re.IGNORECASE) and 
                            not re.search(r' ?hr\b', string_after, re.IGNORECASE) and 
                            not (r' ?(packs|L|psv|puffs|pts|patients|range|scale|dose|doses|cultures|blood|mls|liters|litres|pts|drinks|beers|per|esophagus|tabs|tablets|systolic|sem|strength|bottles|times|drop|cc|up|mg|\/hr|\/hour|mcg|ug|mm|PEEP|hr|hrs|hour|hours|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', string_after, re.IGNORECASE)
                        ):
                            add_type(PHI(m.start(3), m.end(5), Date(m.group(2), day_or_year, month, None)), 'Month/Day (2)', phi)
                    
                    else:
                        if is_probably_date(string_before, string_after):
                            add_type(PHI(m.start(3), m.end(5), Date(m.group(2), day_or_year, month, None)), 'Month/Day (3)', phi)

                if month <= 12 and month > 0 and len(day_or_year) == 2 and (day_or_year >= 50 or day_or_year <= 30):
                    if is_probably_date(string_before, string_after):
                        add_type(PHI(m.start(3), m.end(5), Date(m.group(2), None, month, day_or_year)), 'Month/Year (2)', phi)


def year_with_context_check(x, phi):
    # YEAR_INDICATOR + yy
    for m in re.finditer(r'\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|avr|x2|x3|CHOLECYSTECTOMY|cva|ca|PTC|PTCA|stent|since|surgery|year) + *(\')?)(\d\d)(\.\d)?((\.|\:)\d{1,2})?\b', x, re.IGNORECASE):
        
        if m.group(5) is None and m.group(6) is None: # avoid decimal places or hh:mm
            add_type(PHI(m.start(4), m.end(4), Date(m.group(4), None, None, int(m.group(4)))), 'Year (2 digits)', phi)

    for m in re.finditer(r'\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|x2|x3|CHOLECYSTECTOMY|cva|ca|in|PTCA|since|from|year) + *)(\d{4})((\,? )\d{4})?\b', x, re.IGNORECASE):
        year_1 = int(m.group(3))
        year_2 = int(m.group(4))

        if year_1 <= valid_year_high and year_1 >= valid_year_low:
            add_type(PHI(m.start(3), m.end(3), Date(m.group(3), None, None, year_1)), 'Year (4 digits)', phi)
            add_type(PHI(m.start(4), m.end(4), Date(m.group(4), None, None, year_2)), 'Year (4 digits)', phi)


def season_year(x, phi):
    seasons = ["winter", "spring", "summer", "autumn", "fall"]

    for season in seasons:
        for m in re.finditer(r'\b((' + season + r')(( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b', x, re.IGNORECASE):
            year = int(m.group(7))

            if len(year) == 4 and year <= valid_year_high and year >= valid_year_low:
                add_type(PHI(m.start(7), m.end(7), Date(m.group(7), None, None, year)), 'Year (4 digits)', phi)
            else:
                add_type(PHI(m.start(7), m.end(7), Date(m.group(7), None, None, year)), 'Year (2 digits)', phi)


def find_time(x, phi):
    for m in re.finditer(r'\b( *)((\d{4}) *)(hours|hr|hrs|h)\b', x, re.IGNORECASE):
        potential_time = int(m.group(3))
        hours = potential_time // 100
        minutes = potential_time % 100

        if potential_time < 2359 and potential_time >= 0:
            add_type(PHI(m.start(3), m.end(3), Time(m.group(3), hours, minutes, None, None)), 'Time (military)', phi)

    for m in re.finditer(r'(([A-Za-z0-9%\/]+)\s[A-Za-z0-9%\/]+\s+)?((\d\d?)\:(\d{2})(\:(\d\d))?)(\s)?(am|pm|p.m.|a.m.)?( *([A-Za-z]+))?', x, re.IGNORECASE):
        
        pre = m.group(1)
        post = m.group(11)

        hours = int(m.group(4))
        minutes = int(m.group(5))
        seconds = int(m.group(6))

        meridiem = m.group(9)

        if meridiem is not None:
            if is_valid_time(hours, minutes, seconds):
                add_type(PHI(m.start(3), m.end(3), Time(m.group(3), hours, minutes, seconds, meridiem)), 'Time', phi)

        elif (
            is_valid_24_hour_time(hours, minutes, seconds) and 
            not is_probably_measurement(pre) and 
            not re.search(r'\bPSV? ', pre, re.IGNORECASE) and 
            not re.search(r'\b(CPAP|PS|range|bipap|pap|pad|rate|unload|ventilation|scale|strength|drop|up|cc|rr|cvp|at|up|in|with|ICP|PSV|of) ', pre, re.IGNORECASE) and 
            not re.search(r' ?(packs|psv|puffs|pts|patients|range|scale|mls|liters|litres|drinks|beers|per|esophagus|tabs|pts|tablets|systolic|sem|strength|times|bottles|drop|drops|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|L|hr|hrs|hour|hours|dose|doses|cultures|blood|bpm|ICP|CPAP|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b', post, re.IGNORECASE)
        ):
            add_type(PHI(m.start(3), m.end(3), Time(m.group(3), hours, minutes, seconds, None)), 'Time', phi)


def monthly(x, phi):
    for m in re.finditer(r'\b(every )((\d|\d{2})(nd|st|th|rd)?(( month)?( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b', x, re.IGNORECASE):
        year = int(m.group(10))

        if len(year) == 4:
            if year >= valid_year_low and year <= valid_year_high:
                add_type(PHI(m.start(10), m.end(10), Date(m.group(10), None, None, year)), 'Year (Monthly 4 digit)', phi)

        else:
            add_type(PHI(m.start(10), m.end(10), Date(m.group(10), None, None, year)), 'Year (Monthly 2 digit)', phi)