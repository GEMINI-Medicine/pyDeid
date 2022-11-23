from .phi_types.names import name_first_pass
from .process_note.find_PHI import find_phi
from .process_note.prune_PHI import prune_phi
from .process_note.replace_PHI import replace_phi
from .phi_types.dates import Date, Time
import pandas as pd
import csv
import json
import os
import io
import time
from typing import *
from pathlib import Path
from tqdm import tqdm
import spacy
import re


def pyDeid(
    original_file: Union[str, Path], 
    note_varname: str, 
    encounter_id_varname: str,
    new_file: Optional[Union[str, Path]] = None, 
    phi_output_file: Optional[Union[str, Path]] = None, 
    note_id_varname: Optional[str] = None, 
    phi_output_file_type: Literal['json', 'csv'] = 'csv',
    custom_dr_first_names: Optional[Set[str]] = None, 
    custom_dr_last_names: Optional[Set[str]] = None, 
    custom_patient_first_names: Optional[Set[str]] = None, 
    custom_patient_last_names: Optional[Set[str]] = None,
    verbose: bool = True,
    named_entity_recognition: bool = False,
    file_encoding: str = 'utf-8',
    read_error_handling: str = None,
    **custom_regexes: str
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
    **custom_regexes
        These are named arguments that will be taken as regexes to be scrubbed from
        the given note. The keyword/argument name itself will be used to label the
        PHI in the `phi_output`. Note that all custom patterns will be repalced with
        `<PHI>`.
    

    Returns
    -------
    None
        Nothing is explicitly returned. Side effects produce a de-identified CSV
        file under `new_file` and PHI replaced under `phi_output_file`.
    """
    if custom_regexes:
        print('Supplied custom regexes through **kwargs (see custom_regexes in docstring):\n')
        for key in custom_regexes:
            print('-', key, ':', custom_regexes[key])
        print('\nThese custom patterns will be replaced with <PHI>.\n')

    # check for nan values in custom namelists
    custom_dr_first_names = {x for x in custom_dr_first_names if x==x} if custom_dr_first_names else None
    custom_dr_last_names = {x for x in custom_dr_last_names if x==x} if custom_dr_last_names else None
    custom_patient_last_names = {x for x in custom_patient_last_names if x==x} if custom_patient_last_names else None
    custom_patient_last_names = {x for x in custom_patient_last_names if x==x} if custom_patient_last_names else None

    if new_file is None:
        new_file = os.path.splitext(original_file)[0] + '__DE-IDENTIFIED.csv'
    else:
        new_file = os.path.splitext(new_file)[0] + '.csv'

    if phi_output_file is None:
        phi_output_file = os.path.splitext(original_file)[0] + '__PHI.' + phi_output_file_type
    else:
        phi_output_file = os.path.splitext(phi_output_file)[0] + + '.' + phi_output_file_type
    
    reader = csv.DictReader(
        open(original_file, newline='', encoding=file_encoding, errors=read_error_handling), 
        delimiter=',', 
        quotechar='"', 
        quoting=csv.QUOTE_MINIMAL
        )

    if phi_output_file_type == 'json':
        if encounter_id_varname is None:
            raise ValueError('An encounter ID varname must be supplied to output PHI as a JSON file. It would be overwritten!')

        if not os.path.isfile(phi_output_file):
            phi_output = {}

            with io.open(phi_output_file, 'w') as file:
                file.write(json.dumps(phi_output))
        else:
            raise ValueError('A PHI output JSON file already exists with the same name.')

    elif phi_output_file_type == "csv":
        # write header
        with open(phi_output_file, 'w', newline='') as o:
            writer = csv.writer(o)
            writer.writerow(
                ['encounter_id', 'note_id', 'phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types']
                )

    with open(new_file, 'a', encoding=file_encoding) as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, lineterminator='\n')
        writer.writeheader()

        if verbose:
            reader = tqdm(reader)
            chars = 0
            notes = 0
            start_time = time.time()

        if named_entity_recognition:
            model = spacy.load("en_core_web_sm")  
        else:
            model = None  

        for row in reader:
            
            original_note = row[note_varname]

            errors = []
            
            try:
                phi = name_first_pass(
                    original_note, 
                    custom_dr_first_names, custom_dr_last_names, custom_patient_first_names, custom_patient_last_names
                    )

                find_phi(original_note, phi, custom_regexes, model)

                prune_phi(original_note, phi)
                surrogates, new_note = replace_phi(original_note, phi, return_surrogates=True)
            except:
                surrogates = pd.DataFrame(columns = ['phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types'])
                new_note = original_note

                if note_id_varname is not None:
                    value = {row[note_id_varname]: surrogates}
                    errors.append((row[encounter_id_varname],row[note_id_varname]))
                elif encounter_id_varname is not None:
                    errors.append(row[encounter_id_varname])

            row[note_varname] = new_note
            writer.writerow(row)

            if phi_output_file_type == 'json':

                key = row[encounter_id_varname]
                if note_id_varname is not None:
                    value = {row[note_id_varname]: surrogates}
                else:
                    value = {1: surrogates}

                phi_output.setdefault(key, value).update(value)

            elif phi_output_file_type == "csv":

                phi_output = pd.DataFrame(surrogates)

                if note_id_varname is not None:
                    phi_output.insert(0, 'note_id', row[note_id_varname])

                if encounter_id_varname is not None:
                    phi_output.insert(0, 'encounter_id', row[encounter_id_varname])

                phi_output.to_csv(phi_output_file, mode = 'a', index = False, header = False)

            if verbose:
                chars += len(original_note)
                notes += 1

                progress = f'Processing encounter {row[encounter_id_varname] if encounter_id_varname else notes}' + (f', note {row[note_id_varname]}' if note_id_varname else "")
                reader.set_description(progress)

        if verbose:
            total_time = time.time() - start_time
            print(
                f"""Diagnostics:
                - chars/s = {chars/total_time}
                - s/note = {total_time/notes}"""
                )

        if phi_output_file_type == 'json':
            json.dump(phi_output, open(phi_output_file, 'w'), indent=4)

        if len(errors) != 0:
            print(
                """WARNING:
                The following encounters could not be de-identified:"""
            )

            for encounter in errors:
                if type(encounter) is tuple:
                    print(f'Encounter ID: {encounter[0]}, Note ID: {encounter[1]}')
                else:
                    print(f'Encounter ID: {encounter}')

            print("Please diagnose these encounters using `deid_string`")


def deid_string(
    x: str,
    custom_dr_first_names: Set[str] = None, 
    custom_dr_last_names: Set[str] = None, 
    custom_patient_first_names: Set[str] = None, 
    custom_patient_last_names: Set[str] = None,
    named_entity_recognition: bool = False,
    **custom_regexes: str
    ):
    """Remove and replace PHI from a single string for debugging

    Parameters
    ----------
    x
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
    **custom_regexes
        These are named arguments that will be taken as regexes to be scrubbed from
        the given note. The keyword/argument name itself will be used to label the
        PHI in the `phi_output`. Note that all custom patterns will be repalced with
        `<PHI>`.
    
    
    Returns
    -------
    None
        A tuple where the first element is a dictionary of found PHI and the second element
        is the deidentified string.
    """

    if custom_regexes:
        print('Supplied custom regexes through **kwargs (see custom_regexes in docstring):\n')
        for key in custom_regexes:
            print('-', key, ':', custom_regexes[key])
        print('\nThese custom patterns will be replaced with <PHI>.\n')

    phi = name_first_pass(
        x,
        custom_dr_first_names, custom_dr_last_names, custom_patient_first_names, custom_patient_last_names
        )

    if named_entity_recognition:
        model = spacy.load("en_core_web_sm")  
    else:
        model = None  

    find_phi(x, phi, custom_regexes, model)

    prune_phi(x, phi)
    surrogates, x_deid = replace_phi(x, phi, return_surrogates=True)

    return surrogates, x_deid


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
    spacy.displacy.render(render_data, style="ent", manual=True)
