from ..phi_types.names import *
from ..phi_types.dates import *
from ..phi_types.addresses import address, postal_code, zip_code
from ..phi_types.contact_info import email, telephone
from ..phi_types.IDs import sin, mrn, ohip, ssn


def find_phi(x, phi, custom_regexes, model=None, types=["names", "dates", "sin", "ohip", "mrn", "locations", "hospitals", "contact", "ssn", "zip"]):
    if "names" in types:
        combine_prefix_and_lastname(phi)
        follows_name_indicator(x, phi)
        lastname_comma_firstname(x, phi)
        multiple_names_following_title(x, phi)
        followed_by_md(x, phi)
        follows_pcp_name(x, phi)
        prefixes(x, phi)
        titles(x, phi)
        follows_first_name(x, phi)
        precedes_last_name(x, phi)
        compound_last_names(x, phi)
        initials(x, phi)
        list_of_names(x, phi)
        if model:
            ner(x, phi, model)
        #recurring_name(phi)
    
    if "dates" in types:
        date(x, phi)
        date_with_context_check(x, phi)
        year_with_context_check(x, phi)
        date_range(x, phi)
        season_year(x, phi)
        monthly(x, phi)
        holiday(x, phi)

    if "times" in types:
        find_time(x, phi)

    if "sin" in types:
        sin(x, phi)
    
    if "ohip" in types:
        ohip(x, phi)

    if "mrn" in types:
        mrn(x, phi)

    if "ssn" in types:
        ssn(x, phi)
    
    if "locations" in types:
        address(x, phi)
        if "zip" in types:
            zip(x, phi)
        else:
            postal_code(x, phi)
    
    if "contact" in types:
        email(x, phi)
        telephone(x, phi)

    for custom_regex in custom_regexes:
        if isinstance(custom_regex, str):
            find_custom(x, custom_regexes[custom_regex], custom_regex, phi)

    return phi