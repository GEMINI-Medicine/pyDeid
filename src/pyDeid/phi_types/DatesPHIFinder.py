from collections import namedtuple
import re
from typing import List
from .PHITypeFinder import PHI, PHITypeFinder, PHIDict
from .utils import is_probably_measurement, merge_phi_dicts

Date = namedtuple("Date", ["date_string", "day", "month", "year"])
Time = namedtuple("Time", ["time_string", "hours", "minutes", "seconds", "meridiem"])


class DatesPHIFinder(PHITypeFinder):
    """
    Concrete implementation of PHITypeFinder for detecting dates, years, holidays, seasons.
    """

    seasons = ["winter", "spring", "summer", "autumn", "fall"]
    months = {
        "January": 1,
        "Jan": 1,
        "February": 2,
        "Feb": 2,
        "March": 3,
        "Mar": 3,
        "April": 4,
        "Apr": 4,
        "May": 5,
        "June": 6,
        "Jun": 6,
        "July": 7,
        "Jul": 7,
        "August": 8,
        "Aug": 8,
        "September": 9,
        "Sept": 9,
        "Sep": 9,
        "October": 10,
        "Oct": 10,
        "November": 11,
        "Nov": 11,
        "December": 12,
        "Dec": 12,
    }
    days = {
        "1": 31,
        "2": 28,
        "3": 31,
        "4": 30,
        "5": 31,
        "6": 30,
        "7": 31,
        "8": 31,
        "9": 30,
        "10": 31,
        "11": 30,
        "12": 31,
    }

    def __init__(
        self,
        two_digit_threshold=30,
        valid_year_low=1001,
        valid_year_high=2999,
        invalid_time_pre_words: List[str] = None,
        invalid_time_post_words: List[str] = None,
    ):
        super().__init__()
        self.two_digit_threshold = two_digit_threshold
        self.valid_year_low = valid_year_low
        self.valid_year_high = valid_year_high
        self.invalid_time_pre_words = (
            invalid_time_pre_words if invalid_time_pre_words is not None else []
        )
        self.invalid_time_post_words = (
            invalid_time_post_words if invalid_time_post_words is not None else []
        )

    def find(self, text: str) -> PHIDict:
        phi = {}
        merge_phi_dicts(phi, self.date(text))
        merge_phi_dicts(phi, self.date_with_context_check(text))
        merge_phi_dicts(phi, self.year_with_context_check(text))
        merge_phi_dicts(phi, self.date_range(text))
        merge_phi_dicts(phi, self.season_year(text))
        merge_phi_dicts(phi, self.find_time(text))
        merge_phi_dicts(phi, self.monthly(text))
        merge_phi_dicts(phi, self.holiday(text))
        return phi

    def __is_valid_date(self, date):
        if date.year is not None:
            try:  # safe type-casting
                year = int(date.year)
            except:
                return False

            if len(date.year) == 2:

                if year < self.two_digit_threshold:
                    year = 2000 + year
                else:
                    year = 1900 + year
            else:
                year = date.year

            if not self.__is_valid_year(year):
                return False

        if date.month is not None:
            if not self.__is_valid_month(date.month):
                return False

            if date.day is not None:
                if not self.__is_valid_day(date.day):
                    return False

                try:
                    if date.month in self.months:
                        month = self.months[date.month]
                    else:
                        month = int(date.month)
                    day = int(date.day)
                except:
                    return False

                # check validity of February days
                if month == 2:
                    if (
                        (date.year is not None)
                        and ((int(date.year) % 4) == 0)
                        and (int(date.year) != 2000)
                    ):
                        return day <= 29
                    else:
                        return day <= 28
                elif (month == 4) or (month == 6) or (month == 9) or (month == 11):
                    return day <= 30

            return day <= 31

    def __is_valid_year(self, year):
        if isinstance(year, str):
            try:
                year = int(year)
            except:
                return False

        if isinstance(year, int):
            return (year >= self.valid_year_low) and (year <= self.valid_year_high)

    def __is_valid_day(self, day):
        if isinstance(day, str):
            try:
                day = int(day)
            except:
                return False

        if isinstance(day, int):
            return (day < 32) and (day > 0)

    def __is_valid_month(self, month):
        if isinstance(month, str):
            if month in self.months:
                month = self.months[month]
            else:
                try:
                    month = int(month)
                except:
                    return False

        if isinstance(month, int):
            return (month <= 12) and (month > 0)

    def __is_valid_time(self, time, military=False):
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

        if (
            hours >= 0
            and ((hours <= 12) or (military and hours < 24))
            and minutes >= 0
            and minutes < 60
        ):
            if time.seconds is not None:
                try:
                    seconds = int(time.seconds)
                except:
                    return False

                return seconds >= 0 and seconds < 60
            else:
                return True

        return False

    def __is_probably_date(self, string_before: str, string_after: str):
        if (
            not is_probably_measurement(string_before)
            and not re.search(
                r"\b(drop|up|cc|dose|doses|range|ranged|pad|rate|bipap|pap|unload|ventilation|scale|cultures|blood|at|up|with|in|of|RR|ICP|CVP|strength|PSV|SVP|PCWP|PCW|BILAT|SRR|VENT|PEEP\/PS|flowby|drinks|stage) ?",
                string_before,
                re.IGNORECASE,
            )
            and not re.search(
                r" ?(packs|litres|puffs|mls|liters|L|pts|patients|range|psv|scale|beers|per|esophagus|tabs|tablets|systolic|sem|strength|hours|pts|times|drop|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|hr|hrs|hour|hours|bottles|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns|units|amp|qd|chest pain|intensity)\b",
                string_after,
                re.IGNORECASE,
            )
        ):
            return True
        return False

    def holiday(self, text: str):
        phi = {}
        for m in re.finditer(
            r"\bchristmas|thanksgiving|easter|hanukkah|rosh hashanah|ramadan|victoria day|canada day|labour day\b",
            text,
        ):
            phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append("Holiday")
        return phi

    def date(self, text: str):
        phi = {}

        # month/day/year
        for m in re.finditer(r"\b(\d\d?)[\-\/\.](\d\d?)[\-\/\.](\d\d|\d{4})\b", text):
            start = m.start()
            end = m.end()

            month = m.group(1)
            day = m.group(2)
            year = m.group(3)

            date_key = Date(m.group(), day, month, year)

            if not self.__is_valid_date(date_key):
                date_key = Date(
                    m.group(), month, day, year
                )  # try switching month and day

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"(\|\|)", string_before)
                or re.search(r"(\|\|)", string_after)
            ):
                if not (
                    re.search(r"\d[\/\.\-]", string_before)
                    or re.search(r"[\%\/]", string_after)
                    or re.search(r"\S\d", string_after)
                ):
                    if self.__is_valid_date(date_key):
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Month/Day/Year [mm/dd/yy(yy)]"
                        )

        # day/month/year
        for m in re.finditer(r"\b(\d\d?)[\-\/](\d\d?)[\-\/](\d\d|\d{4})\b", text):
            start = m.start()
            end = m.end()

            day = m.group(1)
            month = m.group(2)
            year = m.group(3)

            date_key = Date(m.group(), day, month, year)

            if not self.__is_valid_date(date_key):
                date_key = Date(
                    m.group(), month, day, year
                )  # try switching month and day

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"\d[\/\.\-]", string_before)
                or re.search(r"[\%\/]", string_after)
                or re.search(r"\S\d", string_after)
            ):
                if self.__is_valid_date(date_key):
                    phi.setdefault(PHI(start, end, date_key), []).append(
                        "Day/Month/Year [dd/mm/yy(yy)]"
                    )

        # year/month/day
        for m in re.finditer(r"\b(\d\d|\d{4})[\-\/\.](\d\d?)[\-\/\.](\d\d?)\b", text):
            start = m.start()
            end = m.end()

            year = m.group(1)
            month = m.group(2)
            day = m.group(3)

            date_key = Date(m.group(), day, month, year)

            if not self.__is_valid_date(date_key):
                date_key = Date(
                    m.group(), month, day, year
                )  # try switching month and day

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"(\|\|)", string_before)
                or re.search(r"(\|\|)", string_after)
                or (re.search(r"\S\d", string_after))
            ):
                if self.__is_valid_date(date_key) and (
                    (int(year) > 50) or (int(year) < 6)
                ):
                    prev_chars = text[(start - 4) : start]
                    next_chars = text[end : (end + 11)]

                    if re.search(r"(\d)(\s)?(\|)(\s)?", prev_chars) and re.search(
                        r"\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)", next_chars
                    ):
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Header Date"
                        )

                    else:
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Year/Month/Day [yy(yy)/mm/dd]"
                        )

        # year/day/month
        for m in re.finditer(r"\b(\d\d|\d{4})[\-\/](\d\d?)[\-\/](\d\d?)\b", text):
            start = m.start()
            end = m.end()

            year = m.group(1)
            day = m.group(2)
            month = m.group(3)

            date_key = Date(m.group(), day, month, year)

            if not self.__is_valid_date(date_key):
                date_key = Date(
                    m.group(), month, day, year
                )  # try switching month and day

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"(\|\|)", string_before)
                or re.search(r"(\|\|)", string_after)
                or (re.search(r"\S\d", string_after))
            ):
                if self.__is_valid_date(date_key) and (
                    (int(year) > 50) or (int(year) < 6)
                ):
                    prev_chars = text[(start - 4) : start]
                    next_chars = text[end : (end + 11)]

                    if re.search(r"(\d)(\s)?(\|)(\s)?", prev_chars) and re.search(
                        r"\s\d{2}\:\d{2}\:\d{2}(\s)?(\|)", next_chars
                    ):
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Header Date"
                        )
                    else:
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Year/Month/Day [yy(yy)/dd/mm]"
                        )

        # mm/yyyy
        for m in re.finditer(r"\b((\d\d?)[\-\/](\d{4}))", text):
            start = m.start()
            end = m.end()

            month = m.group(2)
            year = m.group(3)

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"(\|\|)", string_before)
                or re.search(r"(\|\|)", string_after)
            ):

                if not (
                    re.search(r"\d[\/\.\-]", string_before)
                    or re.search(r"[\/\.\%]", string_after)
                ):

                    if self.__is_valid_month(month) and self.__is_valid_year(year):
                        date_key = Date(m.group(), None, month, year)
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Month/Year 1 [mm/yy(yy)]"
                        )

        # yyyy/mm
        for m in re.finditer(r"\b((\d{4})[\-\/](\d\d?))\b", text):
            start = m.start()
            end = m.end()

            year = m.group(2)
            month = m.group(3)

            string_before = text[(start - 2) : start]
            string_after = text[end : (end + 2)]

            if not (
                re.search(r"(\|\|)", string_before)
                or re.search(r"(\|\|)", string_after)
            ):

                if not (
                    re.search(r"\d[\/\.\-]", string_before)
                    or re.search(r"[\/\.\%]", string_after)
                ):

                    if self.__is_valid_month(month) and self.__is_valid_year(year):
                        date_key = Date(m.group(), None, month, year)
                        phi.setdefault(PHI(start, end, date_key), []).append(
                            "Year/Month 1 [yy(yy)/mm]"
                        )

        for month in self.months:
            # 2-May-04
            for m in re.finditer(
                r"\b((\d{1,2})[ \-]?" + month + r"[ \-\,]? ?\'?(\d{2,4}))\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(2)
                year = m.group(3)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, year)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Day Month Year [dd-Month-yy(yy)]"
                    )

            # May-02-2004
            for m in re.finditer(
                r"\b(" + month + r"[ \-]? ?((\d{1,2})[ \-]?[ \-\,]? ?\'?(\d{4})))\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(3)
                year = m.group(4)

                if self.__is_valid_day(day) and self.__is_valid_year(year):
                    date_key = Date(m.group(), day, month, year)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Month Day Year [Month-dd-yy(yy)]"
                    )

            # Apr. 2 05
            for m in re.finditer(
                r"\b(" + month + r"\b\.? (\d{1,2})[\,\s]+ *\'?(\d{2,4}))\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(2)
                year = m.group(3)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, year)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Month Day Year [Month dd, yy(yy)]"
                    )

            # Apr. 12th 2000
            for m in re.finditer(
                r"\b("
                + month
                + r"\b\.?,?\s*?(\d{1,2})(|st|nd|rd|th|) ?[\,\s]+ *\'?(\d{2,4}))\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(2)
                year = m.group(4)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, year)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Month Day Year (2) [Month dd, yy(yy)]"
                    )

            # Apr. 12th
            for m in re.finditer(
                r"\b(" + month + r"\b\.?,?\s*(\d{1,2})(|st|nd|rd|th|)?)\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(2)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, None)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Month Day [Month dd]"
                    )

            # 12th of April
            for m in re.finditer(
                r"\b((\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b" + month + r")\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(2)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, None)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Day Month [dd of Month]"
                    )

            # 12th of April. 2005
            for m in re.finditer(
                r"\b(((\d{1,2})(|st|nd|rd|th|)?\s+(of\s)?[\-]?\b("
                + month
                + r")\.?,?)\s+(\d{2,4}))\b",
                text,
                re.IGNORECASE,
            ):
                day = m.group(3)
                year = m.group(7)

                if self.__is_valid_day(day):
                    date_key = Date(m.group(), day, month, year)
                    phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                        "Day Month Year (2) [dd of Month, yy(yy)]"
                    )

            # Apr. of 2002
            for m in re.finditer(
                r"\b(" + month + r"\.?,? ?(of )?(\d{2}\d{2}?))\b", text, re.IGNORECASE
            ):
                year = m.group(3)
                date_key = Date(m.group(), None, month, year)

                phi.setdefault(PHI(m.start(), m.end(), date_key), []).append(
                    "Month Year [Month of yy(yy)]"
                )

        return phi

    def date_range(self, text: str):
        phi = {}

        # mm/dd-mm/dd
        for m in re.finditer(r"\b((\d\d?)\/(\d\d?)\-(\d\d?)\/(\d\d?))\b", text):
            date_1 = text[m.start(2) : m.end(3)]
            date_1_key = Date(date_1, m.group(3), m.group(2), None)

            date_2 = text[m.start(4) : m.end(5)]
            date_2_key = Date(date_2, m.group(5), m.group(4), None)

            if self.__is_valid_date(date_1_key) and self.__is_valid_date(date_2_key):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                    "Date range (1)"
                )

        # mm/dd/yy-mm/dd/yy or mm/dd/yyyy-mm/dd/yyyy
        for m in re.finditer(
            r"\b((\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b",
            text,
        ):
            date_1 = text[m.start(2) : m.end(4)]
            date_1_key = Date(date_1, m.group(3), m.group(2), m.group(4))

            date_2 = text[m.start(5) : m.end(7)]
            date_2_key = Date(date_2, m.group(6), m.group(5), m.group(7))

            if self.__is_valid_date(date_1_key) and self.__is_valid_date(date_2_key):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                    "Date range (2)"
                )

        # mm/dd-mm/dd/yy or mm/dd-mm/dd/yyyy
        for m in re.finditer(
            r"\b((\d\d?)\/(\d\d?)\-(\d\d?)\/(\d\d?)\/(\d\d|\d\d\d\d))\b", text
        ):
            date_1 = text[m.start(2) : m.end(4)]
            date_1_key = Date(date_1, m.group(3), m.group(2), None)

            date_2 = text[m.start(5) : m.end(7)]
            date_2_key = Date(date_2, m.group(5), m.group(4), m.group(6))

            if self.__is_valid_date(date_1_key) and self.__is_valid_date(date_2_key):
                phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                    "Date range (3)"
                )

        for month in self.months:
            # 1 through 2-May-04
            for m in re.finditer(
                r"\b((\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[ \-]?"
                + month
                + r"[ \-\,]? ?\'?\d{2,4})\b",
                text,
                re.IGNORECASE,
            ):
                day1 = m.group(2)
                day2 = m.group(4)

                if self.__is_valid_day(day1) and self.__is_valid_day(day2):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Date range (4)"
                    )

            # Mar 1 to 2 05
            for m in re.finditer(
                r"\b("
                + month
                + r"\b\.? (\d{1,2}) ?(\-|to|through|\-\>)+ ?(\d{1,2})[\,\s]+ *\'?\d{2,4})\b",
                text,
                re.IGNORECASE,
            ):
                day1 = m.group(2)
                day2 = m.group(4)

                if self.__is_valid_day(day1) and self.__is_valid_day(day2):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Date range (5)"
                    )

            # Apr. 12 -> 22nd
            for m in re.finditer(
                r"\b("
                + month
                + r"\b\.?,? ?(\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?)\b",
                text,
                re.IGNORECASE,
            ):
                day1 = m.group(2)
                day2 = m.group(4)

                if self.__is_valid_day(day1) and self.__is_valid_day(day2):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Date range (6)"
                    )

            # 12th - 2nd of Apr
            for m in re.finditer(
                r"\b((\d{1,2})(|st|nd|rd|th|)? ?(\-|to|through|\-\>)+ ?(\d{1,2})(|st|nd|rd|th|)?( of)?[ \-]\b"
                + month
                + r")\b",
                text,
                re.IGNORECASE,
            ):
                day1 = m.group(2)
                day2 = m.group(5)

                if self.__is_valid_day(day1) and self.__is_valid_day(day2):
                    phi.setdefault(PHI(m.start(), m.end(), m.group()), []).append(
                        "Date range (7)"
                    )

        return phi

    def date_with_context_check(self, text: str):
        phi = {}

        # mm/dd or mm/yy
        for m in re.finditer(
            r"\b([A-Za-z0-9%\/]+ +)?((\d\d?)([\/\-])(\d\d?))\/?\/?( +[A-Za-z]+)?\b",
            text,
        ):
            month = m.group(3)
            day_or_year = m.group(5)

            if (
                m.group(1) is None
                or not re.search(r"\b(cvp|noc|\%|RR|PCW)", m.group(1), re.IGNORECASE)
            ) and (
                m.group(6) is None
                or not re.search(r"\bpersantine\b", m.group(6), re.IGNORECASE)
            ):
                context_len = 12
                chars_before = text[(m.start(3) - 2) : m.start(3)]
                chars_after = text[m.end(5) : (m.end(5) + 2)]

                if (
                    not re.search(r"\d[\/\.\-]", chars_before)
                    and not re.search(r"[\%]", chars_after)
                    and not re.search(r"\S\d", chars_after)
                ):
                    string_before = text[(m.start(3) - context_len) : m.start(3)]
                    string_after = text[m.end(5) : (m.end(5) + context_len)]
                    date_key = Date(m.group(2), day_or_year, month, None)

                    if not self.__is_valid_date(date_key):
                        date_key = Date(
                            m.group(2), month, day_or_year, None
                        )  # try switching month and day

                    if self.__is_valid_date(date_key):

                        if int(day_or_year) == 5:
                            if (
                                not is_probably_measurement(string_before)
                                and not re.search(
                                    r"\bPSV? ", string_before, re.IGNORECASE
                                )
                                and not re.search(
                                    r"\b(CPAP|PS|range|bipap|pap|pad|rate|unload|ventilation|scale|strength|drop|up|cc|rr|cvp|at|up|in|with|ICP|PSV|of) ",
                                    string_before,
                                    re.IGNORECASE,
                                )
                                and not (
                                    r" ?(packs|psv|puffs|pts|patients|range|scale|mls|liters|litres|drinks|beers|per|esophagus|tabs|pts|tablets|systolic|sem|strength|times|bottles|drop|drops|up|cc|mg|\/hr|\/hour|mcg|ug|mm|PEEP|L|hr|hrs|hour|hours|dose|doses|cultures|blood|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b",
                                    string_after,
                                    re.IGNORECASE,
                                )
                            ):
                                phi.setdefault(
                                    PHI(m.start(3), m.end(5), date_key), []
                                ).append("Month/Day (1) [mm/dd]")

                        elif int(day_or_year) == 2:
                            if (
                                not is_probably_measurement(string_before)
                                and not re.search(
                                    r" ?hour\b", string_after, re.IGNORECASE
                                )
                                and not re.search(
                                    r"\b(with|drop|bipap|pap|range|pad|rate|unload|ventilation|scale|strength|up|cc|rr|cvp|at|up|with|in|ICP|PSV|of) ",
                                    string_before,
                                    re.IGNORECASE,
                                )
                                and not re.search(
                                    r" ?hr\b", string_after, re.IGNORECASE
                                )
                                and not (
                                    r" ?(packs|L|psv|puffs|pts|patients|range|scale|dose|doses|cultures|blood|mls|liters|litres|pts|drinks|beers|per|esophagus|tabs|tablets|systolic|sem|strength|bottles|times|drop|cc|up|mg|\/hr|\/hour|mcg|ug|mm|PEEP|hr|hrs|hour|hours|bpm|ICP|CPAP|years|days|weeks|min|mins|minutes|seconds|months|mons|cm|mm|m|sessions|visits|episodes|drops|breaths|wbcs|beat|beats|ns)\b",
                                    string_after,
                                    re.IGNORECASE,
                                )
                            ):
                                phi.setdefault(
                                    PHI(m.start(3), m.end(5), date_key), []
                                ).append("Month/Day (2) [mm/dd]")

                        else:
                            if self.__is_probably_date(string_before, string_after):
                                phi.setdefault(
                                    PHI(m.start(3), m.end(5), date_key), []
                                ).append("Month/Day (3) [mm/dd]")

                    if (
                        self.__is_valid_month(month)
                        and len(day_or_year) == 2
                        and ((int(day_or_year) >= 50) or (int(day_or_year) <= 30))
                    ):
                        if self.__is_probably_date(string_before, string_after):
                            date_key = Date(m.group(2), None, month, day_or_year)
                            phi.setdefault(
                                PHI(m.start(3), m.end(5), date_key), []
                            ).append("Month/Year (2) [mm/yy]")

        return phi

    def year_with_context_check(self, text: str):
        phi = {}

        # YEAR_INDICATOR + yy
        for m in re.finditer(
            r"\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|avr|x2|x3|CHOLECYSTECTOMY|cva|ca|PTC|PTCA|stent|since|surgery|year) + *(\')?)(\d\d)(\.\d)?((\.|\:)\d{1,2})?\b",
            text,
            re.IGNORECASE,
        ):

            if (
                m.group(5) is None and m.group(6) is None
            ):  # avoid decimal places or hh:mm
                date_key = Date(m.group(4), None, None, m.group(4))
                phi.setdefault(PHI(m.start(4), m.end(4), date_key), []).append(
                    "Year (2 digits)"
                )

        for m in re.finditer(
            r"\b((embolus|mi|mvr|REDO|pacer|ablation|cabg|x2|x3|CHOLECYSTECTOMY|cva|ca|in|PTCA|since|from|year) + *)(\d{4})((\,? )(\d{4}))?\b",
            text,
            re.IGNORECASE,
        ):
            year_1 = m.group(3)

            if self.__is_valid_year(year_1):
                phi.setdefault(
                    PHI(m.start(3), m.end(3), Date(m.group(3), None, None, year_1)), []
                ).append("Year (4 digits)")

                if m.group(4) is not None:
                    year_2 = m.group(6)
                    phi.setdefault(
                        PHI(m.start(4), m.end(4), Date(m.group(4), None, None, year_2)),
                        [],
                    ).append("Year (4 digits)")

        return phi

    def season_year(self, text):
        phi = {}

        for season in self.seasons:
            for m in re.finditer(
                r"\b((" + season + r")(( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b",
                text,
                re.IGNORECASE,
            ):
                year = m.group(7)
                date_key = Date(m.group(7), None, None, year)

                if len(year) == 4 and self.__is_valid_year(year):
                    phi.setdefault(PHI(m.start(7), m.end(7), date_key), []).append(
                        "Year (4 digits)"
                    )
                else:
                    phi.setdefault(PHI(m.start(7), m.end(7), date_key), []).append(
                        "Year (4 digits)"
                    )

        return phi

    def find_time(self, text: str):
        phi = {}

        for m in re.finditer(
            r"\b( *)((\d{4}) *)(hours|hr|hrs|h)\b", text, re.IGNORECASE
        ):
            potential_time = m.group(3)

            if int(potential_time) < 2359 and int(potential_time) >= 0:
                hours = int(potential_time) // 100
                minutes = int(potential_time) % 100
                time_key = Time(m.group(3), hours, minutes, None, None)

                phi.setdefault(PHI(m.start(3), m.end(3), time_key), []).append(
                    "Time (military)"
                )

        for m in re.finditer(
            r"(([A-Za-z0-9%\/]+)\s[A-Za-z0-9%\/]+\s+)?(((\d\d?)\:(\d{2})(\:(\d\d))?)(\s)?(am|pm|p.m.|a.m.)?)( *([A-Za-z]+)\s+)?",
            text,
            re.IGNORECASE,
        ):

            pre = m.group(1)
            post = m.group(12)

            hours = m.group(5)
            minutes = m.group(6)
            seconds = m.group(7)

            meridiem = m.group(10)

            time_key = Time(m.group(4), hours, minutes, seconds, meridiem)

            if meridiem is not None:
                if self.__is_valid_time(time_key):

                    time_key = Time(m.group(3), hours, minutes, seconds, meridiem)
                    phi.setdefault(PHI(m.start(3), m.end(3), time_key), []).append(
                        "Time"
                    )

            elif (
                self.__is_valid_time(time_key, military=True)
                and (
                    pre is None
                    or (
                        not is_probably_measurement(pre)
                        and not re.search(r"\bPSV? ", pre, re.IGNORECASE)
                        and not (pre.lower() in self.invalid_time_pre_words)
                    )
                )
                and (
                    post is None or (not (post.lower() in self.invalid_time_post_words))
                )
            ):
                phi.setdefault(PHI(m.start(4), m.end(4), time_key), []).append("Time")

        return phi

    def monthly(self, text: str):
        phi = {}

        for m in re.finditer(
            r"\b(every )((\d|\d{2})(nd|st|th|rd)?(( month)?( +)of( +))? ?\,?( ?)\'?(\d{2}|\d{4}))\b",
            text,
            re.IGNORECASE,
        ):
            year = m.group(10)
            date_key = Date(m.group(10), None, None, year)

            if len(year) == 4:
                if self.__is_valid_year(year):
                    phi.setdefault(PHI(m.start(10), m.end(10), date_key), []).append(
                        "Year (Monthly 4 digit)"
                    )

            else:
                phi.setdefault(PHI(m.start(10), m.end(10), date_key), []).append(
                    "Year (Monthly 2 digit)"
                )

        return phi

    def find(self):
        phi: PHIDict = {}

        for fn in (
            self.holiday,
            self.date,
            self.date_range,
            self.date_with_context_check,
            self.year_with_context_check,
            self.season_year,
            self.find_time,
            self.monthly,
        ):
            merge_phi_dicts(phi, fn(self.note))

        return phi

    @property
    def name(self):
        pass
