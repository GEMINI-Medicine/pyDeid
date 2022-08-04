from .phi_types.names import name_first_pass
from .phi_types.utils import find_custom
from .process_note.find_PHI import find_phi
from .process_note.prune_PHI import prune_phi
from .process_note.replace_PHI import replace_phi
import pandas as pd
import csv
import json
import os
import io
import time
from typing import *
from pathlib import Path


def pyDeid(
    original_file: Union[str, Path], 
    new_file: Union[str, Path], 
    phi_output_file: Union[str, Path], 
    note_varname: str, 
    encounter_id_varname: str,
    note_id_varname: str = None, 
    mode: Literal['diagnostic', 'performance'] = 'diagnostic',
    custom_dr_first_names: Set[str] = None, 
    custom_dr_last_names: Set[str] = None, 
    custom_patient_first_names: Set[str] = None, 
    custom_patient_last_names: Set[str] = None,
    **custom_regexes: str
    ):
    """Remove and replace PHI from free text

    Parameters
    ----------
    original_file
        Path to the original file containing all PHI in CSV format.
    new_file
        Desired path to write the output CSV.
    phi_output_file
        If `mode == 'diagnostic'`, the desired path to write the output JSON.
        If `mode == 'performance'`, the desired path to write the output CSV.
    note_varname
        Column name in `original_file` with the free text note to de-identify.
    encounter_id_varname
        Column name in `original_file` with the encounter-level ID. Could be
        any identifier column (may not necessariliy be unique).
    note_id_varname
        Column name in `original_file` with the note-level ID. Could be any
        unique identifier column.
    mode
        If `'diagnostic'`, will print runtime performance statistics, as well as
        format the `phi_output_file` into an efficient JSON nested data structure,
        which is lighter on disk space.
        If `'performance'`, will not print any statistics and will output a tidy
        dataframe formatted as a CSV to `phi_output_file`. This data structure
        contains redundant information, but is lighter on memory.
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
    **custom_regexes
        These are named arguments that will be taken as regexes to be scrubbed from
        the given note. The keyword/argument name itself will be used to label the
        PHI in the `phi_output`. Note that all custom patterns will be repalced with
        `<PHI>`.
    

    Returns
    -------
    None
        Nothing is explicitly return. Side effects produce a de-identified CSV
        file under `new_file` and PHI replaced under `phi_output_file`.
    """
    if custom_regexes:
        print('Supplied custom regexes through **kwargs (see custom_regexes in docstring):\n')
        for key in custom_regexes:
            print('-', key, ':', custom_regexes[key])
        print('\nThese custom patterns will be replaced with <PHI>.\n')

    reader = csv.DictReader(
        open(original_file, newline='', encoding='utf-8'), 
        delimiter=',', 
        quotechar='"', 
        quoting=csv.QUOTE_MINIMAL
        )

    if mode == 'diagnostic':
        if not os.path.isfile(phi_output_file):
            phi_output = {}

            with io.open(phi_output_file, 'w') as file:
                file.write(json.dumps(phi_output))
        else:
            raise ValueError("The JSON filename specified already exists.")

        chars = 0
        notes = 0
        start_time = time.time()

    elif mode == "performance":
        # write header
        with open(phi_output_file, 'w', newline='') as o:
            writer = csv.writer(o)
            writer.writerow(
                ['encounter_id', 'note_id', 'phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types']
                )

    with open(new_file, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, lineterminator='\n')
        writer.writeheader()

        for row in reader:
            
            original_note = row[note_varname]

            errors = []
            
            try:
                phi = name_first_pass(
                    original_note, 
                    custom_dr_first_names, custom_dr_last_names, custom_patient_first_names, custom_patient_last_names
                    )
                find_phi(original_note, phi, custom_regexes)

                prune_phi(original_note, phi)
                surrogates, new_note = replace_phi(original_note, phi, return_surrogates=True)
            except:
                pd.DataFrame(columns = ['phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types'])
                new_note = original_note

                if note_id_varname is not None:
                    value = {row[note_id_varname]: surrogates}
                    errors.append((row[encounter_id_varname],row[note_id_varname]))
                else:
                    errors.append(row[encounter_id_varname])

            row[note_varname] = new_note
            writer.writerow(row)

            if mode == 'diagnostic':
                chars += len(original_note)
                notes += 1

                key = row[encounter_id_varname]
                if note_id_varname is not None:
                    value = {row[note_id_varname]: surrogates}
                else:
                    value = {1: surrogates}

                phi_output.setdefault(key, value).update(value)

            elif mode == "performance":

                phi_output = pd.DataFrame(surrogates)

                if note_id_varname is not None:
                    phi_output.insert(0, 'note_id', row[note_id_varname])
                else:
                    phi_output.insert(0, 'note_id', 1)

                phi_output.insert(0, 'encounter_id', row[encounter_id_varname])

                phi_output.to_csv(phi_output_file, mode = 'a', index = False, header = False)

        if mode == 'diagnostic':
            total_time = time.time() - start_time
            print(
                f"""Diagnostics:
                - chars/s = {chars/total_time}
                - s/note = {total_time/notes}"""
                )
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
    **custom_regexes: str
    ):
    """Remove and replace PHI from a single string for debugging

    Parameters
    ----------
    x
        Path to the original file containing all PHI in CSV format.
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
    find_phi(x, phi, custom_regexes)

    prune_phi(x, phi)
    surrogates, x_deid = replace_phi(x, phi, return_surrogates=True)

    return surrogates, x_deid
