import re
from collections import namedtuple
from phi_types.utils import add_type, PHI


two_digit_threshold = 30
valid_year_low = 1900
valid_year_high = 2050

Date = namedtuple("Date", ["date_string", "day", "month", "year"])

months = {"January":1, "Jan":1, "February":2, "Feb":2, "March":3, "Mar":3, "April":4, "Apr":4, "May":5, "June":6, "Jun":6, "July":7, "Jul":7, "August":8, "Aug":8, "September":9, "Sept":9, "Sep":9, "October":10, "Oct":10, "November":11, "Nov":11, "December":12, "Dec":12}

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
            if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'\A[\%\/]', string_after) or re.search(r'\S\d', string_after)):
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

        if not (re.search(r'\d[\/\.\-]', string_before) or re.search(r'\A[\%\/]', string_after) or re.search(r'\S\d', string_after)):
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
