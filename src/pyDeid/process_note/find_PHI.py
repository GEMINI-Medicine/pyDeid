from ..phi_types.names import *
from ..phi_types.dates import *
from ..phi_types.addresses import address, postal_code, hospital, hospital_acronyms
from ..phi_types.contact_info import email, telephone
from ..phi_types.IDs import sin, mrn, ohip


def find_phi(x, phi, custom_regexes, model=None):
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
    
    date(x, phi)
    date_with_context_check(x, phi)
    year_with_context_check(x, phi)
    date_range(x, phi)
    season_year(x, phi)
    find_time(x, phi)
    monthly(x, phi)
    holiday(x, phi)
    
    sin(x, phi)
    ohip(x, phi)
    mrn(x, phi)
    
    postal_code(x, phi)
    address(x, phi)
    hospital(x, phi)
    print(phi)
    
    email(x, phi)
    telephone(x, phi)

    for custom_regex in custom_regexes:
        if isinstance(custom_regex, str):
            find_custom(x, custom_regexes[custom_regex], custom_regex, phi)

    return phi