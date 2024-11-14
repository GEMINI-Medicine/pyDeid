from typing import *
from pathlib import Path
from .pyDeidBuilder import pyDeidBuilder
from .phi_types.utils import CustomRegex
import re
import os

def pyDeid(
    original_file: Union[str, Path], 
    encounter_id_varname: str = "genc_id",
    note_varname: str = "note_text", 
    note_id_varname: Optional[str] = None,
    enable_replace: bool = True,
    return_surrogates: bool = True,
    max_field_size: Union[Literal['auto', 131072], int] = 131072,
    file_encoding: str = 'utf-8',
    read_error_handling: str = None,
    new_file: Optional[Union[str, Path]] = None, 
    phi_output_file: Optional[Union[str, Path]] = None, 
    phi_output_file_type: Literal['json', 'csv'] = 'csv',
    mll_file:Optional[str] = None,
    named_entity_recognition: bool = False,
    two_digit_threshold:int = 30,
    valid_year_low: int = 1900,
    valid_year_high:int = 2050,
    custom_dr_first_names: Optional[Set[str]] = None, 
    custom_dr_last_names: Optional[Set[str]] = None, 
    custom_patient_first_names: Optional[Set[str]] = None, 
    custom_patient_last_names: Optional[Set[str]] = None,
    verbose: bool = True,
    types: List[str] = ["names", "dates", "sin", "ohip", "mrn", "locations", "hospitals", "contact"],
    encounter_id_varname_mll: Optional[str] = 'genc_id',
    **custom_regexes: Union[CustomRegex, str],
    ):
    """Remove and replace PHI from free text

    Parameters
    ----------
    original_file
        Path to the original file containing all PHI in CSV format.
    new_file
        Desired path to write the output CSV. If not supplied, will default to
        `{original filename without extension}__DEID.csv`.
    phi_output_file
        If `phi_output_file_type == 'json'`, the desired path to write the output JSON.
        If `phi_output_file_type == 'csv'`, the desired path to write the output CSV. 
        If not supplied, will default to:
            `{original filename without extension}__PHI.{phi_output_file_type}`.
    note_varname
        Column name in `original_file` with the free text note to de-identify.
    encounter_id_varname
        Column name in `original_file` with the encounter-level ID. Could be
        any identifier column (may not necessariliy be unique).
    note_id_varname
        Column name in `original_file` with the note-level ID. Could be any
        unique identifier column.
    phi_output_file_type
        If `'json'`, will format the `phi_output_file` into an efficient JSON nested 
        data structure, which is lighter on disk space.
        If `'csv'`, will output a tidy dataframe formatted as a CSV to `phi_output_file`. 
        This data structure contains redundant information, but is lighter on memory.
    custom_dr_first_names
        (Optional) set containing site-specific physician first names, generally taken 
        from the physician mapping file. This set should exist in RAM and  will remain 
        in RAM during de-identification.
    custom_dr_last_names
        (Optional) set similar to `custom_dr_first_names`.
    custom_patient_first_names
        (Optional) set containing site-specific patient first names, generally taken 
        from the master linking log. This set should exist in RAM and  will remain 
        in RAM during de-identification.
    custom_patient_last_names
        (Optional) set similar to `custom_patient_first_names`.
    verbose
        Show a progress bar while running through the file with information about the current
        note being processed.
    named_entity_recognition
        Whether to use NER as implemented in the spaCy package for better detection of names.
    file_encoding
        Specify a non-default ('utf8') encoding for the file being read, and therefore the file
        to which the result is being written.
    read_error_handling
        For characters in the input file which do not match the specified system default encoding.
        See python built-in `open` documentation. Use `ignore` to skip, `replace` to pick a 
        placeholder character, etc.
    max_field_size
        For very large notes, prevents _csv.Error: field larger than field limit. 'auto' will find the
        max size that does not result in an OverflowError. The default is usually 131072.
    regex_replace
        Indicate if replacing PHIs using regex is desired or not
    mll_file
        Filepath for MLL if the MLL replacement option is desired.
    **custom_regexes
        These are named arguments that will be taken as regexes to be scrubbed from
        the given note. The keyword/argument name itself will be used to label the
        PHI in the `phi_output`. Note that all custom patterns will be replaced with
        `<PHI>`.

    Returns
    -------
    None
        Nothing is explicitly returned. Side effects produce a de-identified CSV
        file under `new_file` and PHI replaced under `phi_output_file`.
    """
    file_path = os.path.expanduser(original_file)
    builder = pyDeidBuilder() \
        .replace_phi(enable_replace, return_surrogates) \
        .set_input_file(original_file=file_path,
            encounter_id_varname=encounter_id_varname,
            note_varname=note_varname,
            note_id_varname=note_id_varname,
            max_field_size=max_field_size,
            file_encoding=file_encoding,
            read_error_handling=read_error_handling,) \
        .set_phi_types(types)
    
  
    if new_file:
        builder.set_deid_output_file(new_file)
    else:
        builder.set_deid_output_file()

    if phi_output_file:
        builder.set_phi_output_file(phi_output_file, phi_output_file_type)
    else:
        builder.set_phi_output_file()


    if custom_dr_first_names or custom_dr_last_names or custom_patient_first_names or custom_patient_last_names:
        builder.set_custom_namelists(
            custom_dr_first_names,
            custom_dr_last_names,
            custom_patient_first_names,
            custom_patient_last_names
        )

    if named_entity_recognition:
        from spacy import load
        nlp = load("en_core_web_sm")
        builder.set_ner_pipeline(nlp)

    if mll_file and encounter_id_varname_mll:
        mll_file = os.path.expanduser(mll_file)
        builder.set_mll(
            mll_file,
            encounter_id_varname_mll,
            file_encoding,
            read_error_handling,
        )

    if custom_regexes:
        for custom_regex_id in custom_regexes:
            custom_reg = custom_regexes[custom_regex_id]
            if custom_reg.arguments:
                arg_list =custom_reg.arguments.strip().split(',')
            else:
                arg_list =[]
            arguments = [
                arg.strip("'") for arg in arg_list
            ]  # Remaining parts are arguments

            evaluated_args = []
            for arg in arguments:
                try:
                    evaluated_args.append(eval(arg))
                except:
                    evaluated_args.append(arg)

            builder.set_custom_regex(custom_reg.pattern, custom_reg.phi_type, custom_reg.surrogate_builder_fn, evaluated_args)
    

    deid = builder.set_valid_years(
        two_digit_threshold, valid_year_low, valid_year_high
    ).build()

    deid.run(verbose)


def deid_string(

    note: str,
    custom_dr_first_names: Set[str] = None, 
    custom_dr_last_names: Set[str] = None, 
    custom_patient_first_names: Set[str] = None, 
    custom_patient_last_names: Set[str] = None,
    named_entity_recognition: bool = False,
    two_digit_threshold:int = 30,
    valid_year_low: int = 1900,
    valid_year_high:int = 2050,
    types: List[str] = ["names", "dates", "sin", "ohip", "mrn", "locations", "hospitals", "contact"],
    **custom_regexes: str
    ):
    """Remove and replace PHI from a single string for debugging

    Parameters
    ----------
    note
        String with PHI to de-identify.
    custom_dr_first_names
        (Optional) set containing site-specific physician first names, generally taken 
        from the physician mapping file. This set should exist in RAM and  will remain 
        in RAM during de-identification.
    custom_dr_last_names
        (Optional) set similar to `custom_dr_first_names`.
    custom_patient_first_names
        (Optional) set containing site-specific patient first names, generally taken 
        from the master linking log. This set should exist in RAM and  will remain 
        in RAM during de-identification.
    custom_patient_last_names
        (Optional) set similar to `custom_patient_first_names`.
    named_entity_recognition
        Whether to use NER as implemented in the spaCy package for better detection of names.
    detect_only
        Boolean to decide on whether to only output detected phis
    **custom_regexes
        These are named arguments that will be taken as regexes to be scrubbed from
        the given note. The keyword/argument name itself will be used to label the
        PHI in the `phi_output`. Note that all custom patterns will be repalced with
        `<PHI>`.
    
    
    Returns
    -------
    None
        If detect_only=True, then only output a dictionary of found PHIs
        else A tuple where the first element is a dictionary of found PHI and the second element
        is the deidentified string.
    """

    if custom_regexes:
        print('Supplied custom regexes through **kwargs (see custom_regexes in docstring):\n')
        for key in custom_regexes:
            print('-', key, ':', custom_regexes[key])
        print('\nThese custom patterns will be replaced with <PHI>.\n')

    
    builder = pyDeidBuilder() \
        .replace_phi() \
        .set_phi_types(types)
    


    if custom_dr_first_names or custom_dr_last_names or custom_patient_first_names or custom_patient_last_names:
        builder.set_custom_namelists(
            custom_dr_first_names,
            custom_dr_last_names,
            custom_patient_first_names,
            custom_patient_last_names
        )

    if named_entity_recognition:
        from spacy import load
        nlp = load("en_core_web_sm")
        builder.set_ner_pipeline(nlp)

    
    if custom_regexes:
        for custom_regex_id in custom_regexes:
            custom_reg = custom_regexes[custom_regex_id]
            if custom_reg.arguments:
                arg_list =custom_reg.arguments.strip().split(',')
            else:
                arg_list =[]
            arguments = [
                arg.strip("'") for arg in arg_list
            ]  # Remaining parts are arguments

            evaluated_args = []
            for arg in arguments:
                try:
                    evaluated_args.append(eval(arg))
                except:
                    evaluated_args.append(arg)

            builder.set_custom_regex(custom_reg.pattern, custom_reg.phi_type, custom_reg.surrogate_builder_fn, evaluated_args)
    

    deid = builder.set_valid_years(
        two_digit_threshold, valid_year_low, valid_year_high
    ).build()


    surrogates, new_note = deid.handler.handle_string(note)

    return surrogates, new_note


def reid_string(x: str, phi: List[Dict[str, Union[int, str]]]):
    """Replace surrogates from a single string with original PHI

    Parameters
    ----------
    x
        String with surrogates to re-identify.
    phi
        A list of dictionaries with start and end positions for the original PHI in the
        original string, the PHI itself which was replaced, and the start and end
        positions for the surrogate it was replaced with. This type of data structure is
        the same as what is output by `deid_string`.

    Returns
    -------
    str
        The original string which was de-identified, with surrogates replaced with
        original PHI.
    """
    phi_sorted = sorted(phi, key = lambda x: x['surrogate_end'], reverse = True)

    i = 0
    res = ''

    while i < len(phi_sorted):
        
        end = phi_sorted[i]['surrogate_end']
        replace_w = phi_sorted[i]['phi']
        
        if isinstance(replace_w, Date):
            replace_w = replace_w.date_string
        elif isinstance(replace_w, Time):
            replace_w = replace_w.time_string
        
        if i == 0:
            res = replace_w + x[end:] + res
        else:
            prev_start = phi_sorted[i-1]['surrogate_start']
            prev_end = phi_sorted[i-1]['surrogate_end']
            
            res = replace_w + x[end:prev_start] + res
            
        i += 1
        
    return res


def display_deid(original_string, phi):
    """Visualize pyDeid output with the help of spaCy

    Parameters
    ----------
    original_string
        Text which was passed through a de-identification function.
    phi
        A list of dictionaries with start and end positions for the original PHI in the
        original string, the PHI itself which was replaced, and the start and end
        positions for the surrogate it was replaced with. This type of data structure is
        the same as what is output by `deid_string`.
        
    """
    ents = []
    for ent in phi:
        e = {}
        # add the start and end positions of the entity
        e["start"] = ent["phi_start"]
        e["end"] = ent["phi_end"]

        if any(re.search('MRN|SIN|OHIP', line) for line in ent["types"]):
            e["label"] = 'ID'
        
        elif any(re.search('Telephone/Fax', line) for line in ent["types"]):
            e["label"] = 'PHONE'
        
        elif any(re.search('Email Address', line) for line in ent["types"]):
            e["label"] = 'EMAIL'
        
        elif any(re.search('Address|Location|Postalcode', line) for line in ent["types"]):
            e["label"] = 'LOC'
        
        elif any(re.search('(First Name)|(Last Name)|(Name Prefix)|(Name)', line) for line in ent["types"]):
            e["label"] = 'NAME'
        
        elif any(re.search(r'day|month|year|Holiday', line, re.IGNORECASE) for line in ent["types"]):
            e["label"] = 'DATE'

        elif any(re.search('Time', line, re.IGNORECASE) for line in ent["types"]):
            e["label"] = 'TIME'

        else:
            e["label"] = 'PHI'

        ents.append(e)
        
    # construct data required for displacy.render() method
    render_data = [
    {
      "text": original_string,
      "ents": ents,
      "title": None,
    }
    ]
    # spacy.displacy.render(render_data, style="ent", manual=True)

