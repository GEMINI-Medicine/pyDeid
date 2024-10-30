import csv
import time
from typing import *
from tqdm import tqdm


class Deidentifier:
    def __init__(self):
        # remove this, and check all files for removing similar structure

        self.verbose = True
        self.note_id_varname = None
        self.regex_replace = True
        self.reader_dict = {}
        self.encounter_id_varname = ""
        self.note_varname = ""
        self.handler = None
        self.phi_output_file_type = "csv"
        self.phi_output_file = None
        self.deidentified_file = None
        self.encoding = "utf-8"
        self.input_file_type = "csv"
        self.return_surrogates = True

    def run(self, verbose=True):
        """
        Generic run function that will direct to the appropriate `._run_on_X()` method depending on the input
        file type.

        Currently we only support CSVs but this will allow us to expand to XML, etc.

        Args:
            verbose (logical): Whether or not to print a progress bar with de-identification progress updates.
        """

        if self.input_file_type == "csv":
            self._run_on_csv(verbose)

    def _run_on_csv(self, verbose=True):  # our new pyDeid function

        # with open(self.deidentified_file, "wb") as f:
        #     f.write(b'\xff\xfe')  # Write the BOM for UTF-16

        with open(self.deidentified_file, "w", encoding=self.encoding) as f:
            writer_deid_dict = csv.DictWriter(
                f, fieldnames=self.reader_dict.fieldnames, lineterminator="\n"
            )
            writer_deid_dict.writeheader()

            if self.verbose:
                self.reader_dict = tqdm(self.reader_dict)
                chars = 0
                notes = 0
                start_time = time.time()

            errors = []
            # Perform the actions
            for row in self.reader_dict:

                original_note = row[self.note_varname]

                # TODO: things to pass which has no member varible  row, errors
                errors, surrogates, new_note, found_phis = self.handler.handle_csv_row(
                    row,
                    errors,
                    self.encounter_id_varname,
                    self.note_id_varname,
                    self.note_varname,
                   
                )

                self._write_new_note_to_file(
                    found_phis, surrogates, row, writer_deid_dict, new_note
                )

                chars, notes = self._display_processing_encounter(
                    chars, notes, row, original_note
                )

            if self.verbose:
                total_time = time.time() - start_time
                print(
                    f"""Diagnostics:
                        - chars/s = {chars/total_time}
                        - s/note = {total_time/notes}"""
                )

            if len(errors) != 0:
                print(
                    """WARNING:
                        The following encounters could not be de-identified:"""
                )

                for encounter in errors:
                    if type(encounter) is tuple:
                        print(f"Encounter ID: {encounter[0]}, Note ID: {encounter[1]}")
                    else:
                        print(f"Encounter ID: {encounter}")

                print("Please diagnose these encounters using `deid_string`")

    def _display_processing_encounter(self, chars, notes, row, original_note):
        if self.verbose:
            chars += len(original_note)
            notes += 1

            progress = (
                f"Processing encounter {row[self.encounter_id_varname] if self.encounter_id_varname else notes}"
                + (
                    f", note {row[self.note_id_varname]}"
                    if self.note_id_varname
                    else ""
                )
            )
            self.reader_dict.set_description(progress)
        return chars, notes

    def _write_new_note_to_file(
        self, found_phis, surrogates, row, writer_deid_dict, new_note
    ):
        if not  self.return_surrogates :  # Write outputs for regex find
            if self.regex_replace:
                row[self.note_varname] = new_note
                writer_deid_dict.writerow(row)
                self._write_to_file(found_phis, row)
            else:
                self._write_to_file(found_phis, row)
        else:  # Write outputs for regex replacement
            row[self.note_varname] = new_note
            writer_deid_dict.writerow(row)
            self._write_to_file(surrogates, row)

    def _write_to_file(self, items, row):
   
        if self.phi_output_file_type == "csv":
            with open(self.phi_output_file, "r", newline="") as out:
                reader = csv.DictReader(out)
                fields = reader.fieldnames

            for d in items:
                if self.note_id_varname is not None:
                    if d.get("note_id") is None:
                        d.setdefault("note_id", row[self.note_id_varname])
                else:
                    d.setdefault("note_id", "NULL")

                if self.encounter_id_varname is not None:
                    if d.get("encounter_id") is None:
                        d.setdefault("encounter_id", row[self.encounter_id_varname])

            with open(self.phi_output_file, "a", newline="") as write_file:
                writer = csv.DictWriter(write_file, fieldnames=fields)
                for d in items:
                    writer.writerow(d)
