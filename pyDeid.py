from phi_types.names import name_first_pass
from process_note.find_PHI import find_phi
from process_note.prune_PHI import prune_phi
from process_note.replace_PHI import replace_phi
import csv
import json
import os
import io
import time


def pyDeid(original_file, new_file, phi_output_file, note_varname, encounter_id_varname, note_id_varname=None, mode='diagnostic'):
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

        chars = 0
        notes = 0
        start_time = time.time()

    writer = csv.DictWriter(open(new_file, 'w'), fieldnames=reader.fieldnames, lineterminator='\n')
    writer.writeheader()

    for row in reader:
        
        original_note = row[note_varname]

        phi = name_first_pass(original_note)
        find_phi(original_note, phi)
        prune_phi(original_note, phi)
        surrogates, new_note = replace_phi(original_note, phi, return_surrogates=True)

        if mode == 'diagnostic':
            chars += len(original_note)
            notes += 1

            key = row[encounter_id_varname]
            if note_id_varname is not None:
                value = {row[note_id_varname]: surrogates}
            else:
                value = {1: surrogates}

            phi_output.setdefault(key, value).update(value)
            
        row[note_varname] = new_note
        writer.writerow(row)

    if mode == 'diagnostic':
        total_time = time.time() - start_time
        print(
            f"""Diagnostics:
              - chars/s = {chars/total_time}
              - s/note = {total_time/notes}"""
            )
        json.dump(phi_output, open(phi_output_file, 'w'), indent=4)

if __name__ == "__main__":
    pyDeid('test.csv', 'deid.csv', 'output.json', 'note_text', 'genc_id', 'note_id')
