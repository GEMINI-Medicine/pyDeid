from .phi_types.names import name_first_pass
from .process_note.find_PHI import find_phi
from .process_note.prune_PHI import prune_phi
from .process_note.replace_PHI import replace_phi
from .process_note.replace_PHI import replace_value
from .process_note.replace_PHI import return_phi
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
import re
import sys


def pyDeid(
    original_file: Union[str, Path], 
    note_varname: str, 
    encounter_id_varname: str,
    new_file: Optional[Union[str, Path]] = None, 
    phi_output_file: Optional[Union[str, Path]] = None, 
    found_phi_output_file: Optional[Union[str, Path]] = None, 
    mll_phi_output_file: Optional[Union[str, Path]] = None, 
    mll_new_file: Optional[Union[str, Path]] = None, 
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
    max_field_size: Union[Literal['auto', 131072], int] = 131072,
    mll_find_replace: bool = False,
    regex_find: bool = True,
    regex_replace: bool = True,
    mll_file: Optional[Union[str, Path]] = None,
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
    found_phi_output_file
        The output file containing the PHIs that have been found in the notes.
        If `'json'`, will format the `phi_output_file` into an efficient JSON nested 
        data structure, which is lighter on disk space.
        If `'csv'`, will output a tidy dataframe formatted as a CSV to `phi_output_file`. 
        This data structure contains redundant information, but is lighter on memory.
    mll_phi_output_file
        The output file containing the PHIs that have been found in the notes using the MLL.
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
    mll_find_replace
        Indicate if using MLL to find and replace PHIs is desired or not
    regex_find 
        Indicate if finding PHIs using regex is desired or not
    regex_replace
        Indicate if replacing PHIs using regex is desired or not
    mll_file
        Filepath for MLL if the MLL replacement option is desired.
    mll_new_file
        Desired path to write the MLL replacement output CSV. If not supplied, will default to
        `{original filename without extension}__MLL_DEID.csv`.
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

    if named_entity_recognition:
        import spacy

    if custom_regexes:
        print('Supplied custom regexes through **kwargs (see custom_regexes in docstring):\n')
        for key in custom_regexes:
            print('-', key, ':', custom_regexes[key])
        print('\nThese custom patterns will be replaced with <PHI>.\n')

    if max_field_size == 'auto':
        maxInt = sys.maxsize

        while True:
            # decrease the maxInt value by factor 10 
            # as long as the OverflowError occurs.

            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)

    elif max_field_size == 131072:
        pass
    
    elif isinstance(max_field_size, int):
        csv.field_size_limit(max_field_size)

    # check for nan values in custom namelists
    custom_dr_first_names = {x for x in custom_dr_first_names if x==x} if custom_dr_first_names else None
    custom_dr_last_names = {x for x in custom_dr_last_names if x==x} if custom_dr_last_names else None
    custom_patient_last_names = {x for x in custom_patient_last_names if x==x} if custom_patient_last_names else None
    custom_patient_first_names = {x for x in custom_patient_first_names if x==x} if custom_patient_first_names else None

    # File for de-identified note
    if new_file is None:
        new_file = os.path.splitext(original_file)[0] + '__DE-IDENTIFIED.csv'
    else:
        new_file = os.path.splitext(new_file)[0] + '.csv'
    temp = open(new_file, "w+")
    temp.close()

    # File for identified PHIs and surrogates
    if phi_output_file is None:
        phi_output_file = os.path.splitext(original_file)[0] + '__PHI.' + phi_output_file_type
    else:
        phi_output_file = os.path.splitext(phi_output_file)[0] + '.' + phi_output_file_type

    # File for de-identified note using MLL
    if mll_new_file is None:
        mll_new_file = os.path.splitext(original_file)[0] + '__MLL_DEID.csv'
    else:
        mll_new_file = os.path.splitext(mll_new_file)[0] + '.csv'
    temp = open(mll_new_file, "w+")
    temp.close()

    # File for outputing the found PHIs from the notes
    if found_phi_output_file is None:
        found_phi_output_file = os.path.splitext(original_file)[0] + '__FOUND_PHI.' + phi_output_file_type
    else:
        phi_output_file = os.path.splitext(phi_output_file)[0] + '.' + phi_output_file_type

    # File for outputing the found PHIs from the notes using MLL
    if mll_phi_output_file is None:
        mll_phi_output_file = os.path.splitext(original_file)[0] + '__MLL_PHI.' + phi_output_file_type
    else:
        phi_output_file = os.path.splitext(phi_output_file)[0] + '.' + phi_output_file_type

    reader = csv.DictReader(
        open(original_file, newline='', encoding=file_encoding, errors=read_error_handling), 
        delimiter=',', 
        quotechar='"', 
        quoting=csv.QUOTE_MINIMAL
        )
    reader_fieldnames = reader.fieldnames  # store reader fieldnames for later use
    
    if mll_file is not None:  # Setup to read MLL file if MLL exists
        mll_find_replace = True
        mll_rows = {}
        mll_reader = csv.DictReader(
            open(mll_file, newline='', encoding=file_encoding, errors=read_error_handling), 
            delimiter=',', 
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL
            )
        for row in mll_reader:
            # Get index for the encounter id for easy retrieval later
            key = row[encounter_id_varname]
            mll_rows[key] = row
    # import ipdb
    # ipdb.set_trace()

    if phi_output_file_type == 'json':
        if encounter_id_varname is None:
            raise ValueError('An encounter ID varname must be supplied to output PHI as a JSON file. It would be overwritten!')

        phi_output = {}
        if not os.path.isfile(phi_output_file):
            with io.open(phi_output_file, 'w') as file:
                file.write(json.dumps(phi_output))
        if not os.path.isfile(found_phi_output_file):
            with io.open(found_phi_output_file, 'w') as file:
                file.write(json.dumps(phi_output))
        if not os.path.isfile(mll_phi_output_file):
            with io.open(mll_phi_output_file, 'w') as file:
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
        with open(found_phi_output_file, 'w', newline='') as o:
            writer = csv.writer(o)
            writer.writerow(
                ['encounter_id', 'phi_start', 'phi_end', 'phi', 'types']
                )
        with open(mll_phi_output_file, 'w', newline='') as o:
            writer = csv.writer(o)
            writer.writerow(
                ['encounter_id', 'phi', 'surrogate', 'types']
                )
    
    # Start Process
    with open(new_file, 'a', encoding=file_encoding) as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, lineterminator='\n')
        writer.writeheader()
        
        # Write headers for de-identified note using MLL
        with open(mll_new_file, 'a', encoding=file_encoding) as j:
            mll_writer = csv.DictWriter(j, fieldnames=reader.fieldnames, lineterminator='\n')
            mll_writer.writeheader()

        if verbose:
            reader = tqdm(reader)
            chars = 0
            notes = 0
            start_time = time.time()

        if named_entity_recognition:
            model = spacy.load("en_core_web_sm")  
        else:
            model = None

        # set default actions if invalid options are given
        if not regex_find and regex_replace:
            print("Cannot perform replacement without finding, removed replacement action")
            regex_find = True
            regex_replace = False
        if (not regex_find and not regex_replace and not mll_find_replace) or (mll_find_replace and mll_file is None):
            print("Invalid actions, changed to default settings (xfr)")
            mll_find_replace = False
            regex_find = True
            regex_replace = True

        mll_surrogates = []
        # Perform the actions
        for row in reader:
            
            original_note = row[note_varname]

            errors = []
            phi = name_first_pass(
                original_note, 
                custom_dr_first_names, custom_dr_last_names, custom_patient_first_names, custom_patient_last_names
                )
            if mll_find_replace:  # If MLL is provided
                # Take the encounter ID from the notes
                enc_id = row[encounter_id_varname]
                # Find the encouter ID from MLL
                mll_vals = mll_rows.get(enc_id)
                # Utilize MLL information to replace all matching information
                if mll_vals is not None:
                    for val in mll_vals:
                        # @TODO Function still needs to directly match with entries in the MLL
                        if val != encounter_id_varname:
                            cur_surrogate, mll_new_note = replace_value(mll_vals[val], val, str(row[note_varname]), phi)
                            mll_surrogates.append({'phi': mll_vals[val], 
                                                'surrogate': cur_surrogate, 
                                                'type': val})
                            row[note_varname] = mll_new_note
                else:
                    print("No MLL entries found")
                    mll_new_note = ''

            if regex_find:  # If regex find is desired
                try:

                    find_phi(original_note, phi, custom_regexes, model)

                    prune_phi(original_note, phi)

                    found_phis = return_phi(original_note, phi, return_surrogates=True)
                
                    if regex_replace:  # Create surrogates if regex replacement is desired
                        surrogates, new_note = replace_phi(original_note, phi, return_surrogates=True)
                
                except:
                    surrogates = pd.DataFrame(columns = ['phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types'])
                    new_note = original_note

                    if note_id_varname is not None:
                        value = {row[note_id_varname]: surrogates}
                        errors.append((row[encounter_id_varname],row[note_id_varname]))
                    elif encounter_id_varname is not None:
                        errors.append(row[encounter_id_varname])
            if mll_find_replace:  # Write outputs from MLL actions
                write_to_file(mll_surrogates, row, encounter_id_varname, note_id_varname, phi_output_file_type, 
                                mll_phi_output_file)
                with open(mll_new_file, 'a', encoding=file_encoding) as j:
                    mll_writer = csv.DictWriter(j, fieldnames=reader_fieldnames, lineterminator='\n')
                    # mll_writer.writeheader()
                    row[note_varname] = mll_new_note
                    mll_writer.writerow(row)
            if regex_find:  # Write outputs for regex find
                write_to_file(found_phis, row, encounter_id_varname, note_id_varname, phi_output_file_type, 
                                found_phi_output_file)
            if regex_replace:  # Write outputs for regex replacement
                row[note_varname] = new_note
                writer.writerow(row)

                write_to_file(surrogates, row, encounter_id_varname, note_id_varname, phi_output_file_type, phi_output_file)
                # if phi_output_file_type == 'json':

                #     key = row[encounter_id_varname]
                #     if note_id_varname is not None:
                #         value = {row[note_id_varname]: surrogates}
                #     else:
                #         value = {1: surrogates}

                #     phi_output.setdefault(key, value).update(value)

                # elif phi_output_file_type == "csv":

                #     phi_output = pd.DataFrame(surrogates)

                #     if note_id_varname is not None:
                #         phi_output.insert(0, 'note_id', row[note_id_varname])

                #     if encounter_id_varname is not None:
                #         phi_output.insert(0, 'encounter_id', row[encounter_id_varname])

                #     phi_output.to_csv(phi_output_file, mode = 'a', index = False, header = False)

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

    # check for nan values in custom namelists
    custom_dr_first_names = {x for x in custom_dr_first_names if x==x} if custom_dr_first_names else None
    custom_dr_last_names = {x for x in custom_dr_last_names if x==x} if custom_dr_last_names else None
    custom_patient_last_names = {x for x in custom_patient_last_names if x==x} if custom_patient_last_names else None
    custom_patient_first_names = {x for x in custom_patient_first_names if x==x} if custom_patient_first_names else None

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
    # spacy.displacy.render(render_data, style="ent", manual=True)

def write_to_file(
        items,
        row,
        encounter_id_varname,
        note_id_varname,
        output_file_type,
        output_file,
        ):
    if output_file_type == 'json':

        key = row[encounter_id_varname]
        if note_id_varname is not None:
            value = {row[note_id_varname]: items}
        else:
            value = {1: items}

        phi_output.setdefault(key, value).update(value)

    elif output_file_type == "csv":

        phi_output = pd.DataFrame(items)

        if note_id_varname is not None:
            phi_output.insert(0, 'note_id', row[note_id_varname])
        else:
            phi_output.insert(0, 'note_id', "NULL")

        if encounter_id_varname is not None:
            phi_output.insert(0, 'encounter_id', row[encounter_id_varname])

        phi_output.to_csv(output_file, mode = 'a', index = False, header = False)
