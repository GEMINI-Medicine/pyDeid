from phi_types.names import name_first_pass
from process_note.find_PHI import find_phi
from process_note.prune_PHI import prune_phi
from process_note.replace_PHI import replace_phi
import csv


def pyDeid(source_filename, target_filename, note_varname):
    reader = csv.DictReader(
        open(source_filename, newline='', encoding='utf-8'), 
        delimiter=',', 
        quotechar='"', 
        quoting=csv.QUOTE_MINIMAL
        )

    writer = csv.DictWriter(open(target_filename, 'w'), fieldnames = reader.fieldnames, lineterminator = '\n')
    writer.writeheader()
    
    for row in reader:
        old_note = row[note_varname]

        phi = name_first_pass(old_note)
        find_phi(old_note, phi)
        prune_phi(old_note, phi)
        res = replace_phi(old_note, phi)

        row[note_varname] = res
        writer.writerow(row)

if __name__ == "__main__":
    pyDeid('test.csv', 'deid.csv', 'note_text')
