from typing import *
from pathlib import Path
import sys
from .Deidentifier import Deidentifier
import csv
import json
import os
from .process_note.PHIFinder import *
from .process_note.PHIHandler import *
from .process_note.PHIPruner import *
from .process_note.PHIReplacer import *
import io
from spacy.language import Language


class pyDeidBuilder:
    def __init__(self):
        """Builder for a Deidentifier object.

        Allows the user to specify the pyDeid features that will be enabled, such as named entity recognition, custom regular expressions,
        custom namelists, and a master linking log.
        """
        self.deid = Deidentifier()
        self.mll_rows = {}
        self.finder = None
        self.pruner = PHIPruner()
        self.replacer = None

        self.original_file = None
        self.phi_types = []
        self.ner_model = None
        
        self.finder_custom_regexes = []
        self.finder_custom_dr_first_names = None
        self.finder_custom_dr_last_names = None
        self.finder_custom_patient_first_names = None
        self.finder_custom_patient_last_names = None
        self.finder_two_digit_threshold = None
        self.finder_valid_year_low = None
        self.finder_valid_year_high = None
        

    def replace_phi(self, enable_replace=True, return_surrogates: bool = True):
        """Replaces found instances of PHI in the note to de-identify.

        Args:
            enable_replace (bool, optional): In the processed, de-identified output file, whether or not to replace all instances of found PHI
                with surrogates. Defaults to True.
            return_surrogates (bool, optional): In the PHI output file, whether or not to output which surrogates the PHI were replaced with.
                Defaults to True.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        if not enable_replace and return_surrogates:
            raise ValueError("Cant return surrogates if replace not enabled")

        if enable_replace:
            self.replacer = PHIReplacer(return_surrogates)
        else:
            self.replacer = None

        self.deid.regex_replace = enable_replace
        self.deid.return_surrogates = return_surrogates

        return self

    def set_input_file(
        self,
        original_file: Union[str, Path],
        encounter_id_varname: str = "genc_id",
        note_varname: str = "note_text",
        note_id_varname: str = None,
        max_field_size: int = 131072,
        file_encoding: str = "utf-8",
        read_error_handling: str = None,
    ):
        """Specify the file to be de-identified.

        Args:
            original_file (Union[str, Path]): The path to the file to de-identify.
            encounter_id_varname (str): The unique identifier column name in the file to de-identify.
            note_varname (str): The column name of the input file that contains the actual note to be de-identified.
            note_id_varname (str, optional): When the input file contains multiple notes per encounter, the unique note identifier. Defaults to None.
            max_field_size (int, optional): Passed to csv.field_size_limit. Defaults to 131072.
            file_encoding (str, optional): Passed to csv.DictReader. Defaults to "utf-8".
            read_error_handling (str, optional): Passed to csv.DictReader. Defaults to None.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        self.original_file = original_file
        self.deid.encoding = file_encoding
        self.deid.note_id_varname = note_id_varname
        self.deid.encounter_id_varname = encounter_id_varname
        self.deid.note_varname = note_varname

        self._load_reader_dict(file_encoding, read_error_handling)
        self.set_max_field_size(max_field_size)

        return self

    def set_deid_output_file(self, new_file: Union[str, Path] = None):
        """Allows for a custom filename for the de-identified output file.

        Args:
            new_file (Union[str, Path], optional): Custom name for the output file. Defaults to None.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        # File for de-identified note
        if new_file is None and self.deid.deidentified_file is None:
            new_file = os.path.splitext(self.original_file)[0] + "__DE-IDENTIFIED.csv"

        elif new_file is not None:
            new_file = os.path.splitext(new_file)[0] + ".csv"

        else:
            return

        self.deid.deidentified_file = new_file

        return self

    def set_phi_output_file(
        self,
        phi_output_file: Union[str, Path] = None,
        phi_output_file_type: Literal["csv"] = "csv",
    ):
        """Allows for a custom filename for the PHI output file.

        Args:
            phi_output_file (_type_, optional): Custom name for the output file. Defaults to None.
            phi_output_file_type (Literal['csv'], optional): What format to output the PHI to. Currently only supports "csv".

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        # File for identified PHIs and surrogates
        if phi_output_file is None and self.deid.phi_output_file is None:
            phi_output_file = (
                os.path.splitext(self.original_file)[0]
                + "__PHI."
                + phi_output_file_type
            )

        elif phi_output_file is not None:
            phi_output_file = (
                os.path.splitext(phi_output_file)[0] + "." + phi_output_file_type
            )

        else:
            return

        self.deid.phi_output_file = phi_output_file
        self.deid.phi_output_file_type = phi_output_file_type
        self._write_headers_phi_output_file(
            self.deid.encounter_id_varname, phi_output_file, phi_output_file_type
        )

        return self

    def _set_file_defaults(self):
        self.set_deid_output_file(new_file=None)
        self.set_phi_output_file(phi_output_file=None)

        return self

    def set_phi_types(self, types: List[str]):
        """Specify which types of PHI to de-identify.

        Args:
            types (List[str]): Currently, pyDeid supports names, dates, sin, ohip, mrn, locations, hospitals, and contact.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        self.phi_types = types

        return self

    def set_mll(
        self,
        filename: Union[str, Path],
        encounter_id_varname: str = "genc_id",
        file_encoding: str = "utf-8",
        read_error_handling: str = None,
        use_namelists: bool = True,
        patient_name_columns: Dict[str, str] = {
            "first_name": "first_name",
            "last_name": "last_name",
        },
        doctor_name_columns: Dict[str, List[str]] = {
            "first_name": ["disphy_first_name", "admphy_first_name", "mrp_first_name"],
            "last_name": ["disphy_last_name", "admphy_last_name", "mrp_last_name"],
        },
    ):
        """Provide a master linking log that has encounter-specific PHI that can be linked to the notes corresponding to that
        encounter for improved PHI detection.

        Args:
            filename (Union[str, Path]): Path to the master linking log. Expected to be in CSV format.
            encounter_id_varname (str): The unique identifier column name in the file to de-identify.
            file_encoding (str, optional): Passed to csv.DictReader. Defaults to "utf-8".
            read_error_handling (str, optional): Passed to csv.DictReader. Defaults to None.
            use_namelists (bool, optional): Use ALL patient and doctor names from the MLL as a namelist for all notes.
            patient_name_columns (dict[str, str], optional): Mapping of name type to column name for patient names.
                Example: {"first_name": "patient_first", "last_name": "patient_last"}
            doctor_name_columns (dict[str, list[str]], optional): Mapping of name type to list of column names for doctor names.
                Example: {
                    "first_name": ["attending_first", "consulting_first"],
                    "last_name": ["attending_last", "consulting_last"]
                }

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.

        Raises:
            ValueError: If encounter_id_varname is not found in the CSV file.
        """

        if use_namelists:
            custom_patient_first_names = set()
            custom_patient_last_names = set()
            custom_dr_first_names = set()
            custom_dr_last_names = set()

            # Create mapping of column names to their respective sets
            name_set_mapping = {
                "first_name": {
                    "patient": custom_patient_first_names,
                    "doctor": custom_dr_first_names,
                },
                "last_name": {
                    "patient": custom_patient_last_names,
                    "doctor": custom_dr_last_names,
                },
            }

        with open(
            filename,
            newline="",
            encoding=file_encoding,
            errors=read_error_handling,
        ) as f:
            mll_reader = csv.DictReader(
                f,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )
          
            # Check if the encounter ID column exists
            if encounter_id_varname not in mll_reader.fieldnames:
                raise ValueError(
                    f"Encounter ID column '{encounter_id_varname}' not found in the CSV file."
                )

            for row in mll_reader:
                # Get index for the encounter id for easy retrieval later
                key = row[encounter_id_varname]
                self.mll_rows[key] = row

                if use_namelists:
                    # Process patient names
                    for name_type, column in patient_name_columns.items():
                        if column in row:
                            value = row[column]
                            if value:  # Only add non-empty values
                                name_set_mapping[name_type]["patient"].add(value)

                    # Process doctor names
                    for name_type, columns in doctor_name_columns.items():
                        for column in columns:
                            if column in row:
                                value = row[column]
                                if value:  # Only add non-empty values
                                    name_set_mapping[name_type]["doctor"].add(value)

            if use_namelists:
                self.set_custom_namelists(
                    custom_patient_first_names,
                    custom_patient_last_names,
                    custom_dr_first_names,
                    custom_dr_last_names,
                )

            return self


    def _load_reader_dict(self, file_encoding="utf-8", read_error_handling=None):
        self.deid.reader_dict = csv.DictReader(
            open(
                self.original_file,
                newline="",
                encoding=file_encoding,
                errors=read_error_handling,
            ),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )

    def _write_headers_phi_output_file(
        self, encounter_id_varname, phi_output_file, phi_output_file_type="csv"
    ):

        if phi_output_file_type == "json":
            if encounter_id_varname is None:
                raise ValueError(
                    "An encounter ID varname must be supplied to output PHI as a JSON file. It would be overwritten!"
                )

            phi_output = {}
            if not os.path.isfile(phi_output_file):
                with io.open(phi_output_file, "w") as file:
                    file.write(json.dumps(phi_output))

            else:
                raise ValueError(
                    "A PHI output JSON file already exists with the same name."
                )

        elif phi_output_file_type == "csv":
            # write header
            with open(phi_output_file, "w", newline="") as o:
                writer = csv.writer(o)
                if (
                    not self.deid.regex_replace and not self.deid.return_surrogates
                ) or (self.deid.regex_replace and not self.deid.return_surrogates):
                    writer.writerow(
                        [
                            "encounter_id",
                            "note_id",
                            "phi_start",
                            "phi_end",
                            "phi",
                            "types",
                        ]
                    )

                else:  # enable is True, return surrogats is True
                    writer.writerow(
                        [
                            "encounter_id",
                            "note_id",
                            "phi_start",
                            "phi_end",
                            "phi",
                            "surrogate_start",
                            "surrogate_end",
                            "surrogate",
                            "types",
                        ]
                    )

    def set_ner_pipeline(self, model: Language = None):
        """Adds a named entity recognition step using a spaCy NER pipeline.

        Args:
            model (Language, optional): Any spaCy NER pipeline. See the "Using spaCy with pyDeid" tutorial for more information.
                Defaults to None.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        self.ner_model = model
        return self

    def set_custom_regex(
        self,
        pattern: str,
        phi_type: str = "custom_regexes",
        surrogate_builder_fn: Callable = None,
        arguments: list = [],
    ):
        """Specify known patterns specific to a file that need to be removed.

        Args:
            pattern (str): A regular expression to be detected in the note.
            phi_type (str, optional): The name of the custom PHI. Defaults to "custom_regex".
            surrogate_builder_fn (Callable, optional): A function that takes no arguments, and returns a random surrogate for
                the phi_type of interest. Defaults to <PHI>.

        Raises:
            ValueError: replace_phi must be called prior to defining custom_regex with a surrogate builder function.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        if not surrogate_builder_fn:

            def surrogate_builder_fn():
                return "<PHI>"

            # TODO: replace with python warning
            print(
                "No surrogate function defined for this custom regex, any identified PII will be replaced with <PHI>\n"
            )

        custom_regex = CustomRegex(phi_type, pattern, surrogate_builder_fn, arguments)

        self.finder_custom_regexes = self.finder_custom_regexes + [custom_regex]

        if self.replacer is None and surrogate_builder_fn is None:
            raise ValueError("surrogate_builder_fn specified but replace_phi not set")

        if self.replacer is not None:
            self.replacer.custom_regexes = self.replacer.custom_regexes + [custom_regex]

        return self

    def set_valid_years(
        self, two_digit_threshold=30, valid_year_low=1900, valid_year_high=2050
    ):
        """Specifies cutoffs for "reasonable" years in the note. When set appropriately, reduces false positives.

        Args:
            two_digit_threshold (int, optional): Lowest expected two digit year. Defaults to 30.
            valid_year_low (int, optional): Lowest expected four digit year. Defaults to 1900.
            valid_year_high (int, optional): Highest expected four digit year. Defaults to 2050.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        self.finder_two_digit_threshold = two_digit_threshold
        self.finder_valid_year_low = valid_year_low
        self.finder_valid_year_high = valid_year_high
        return self

    def _remove_NaN(self, namelist):
        return {x for x in namelist if x == x} if namelist else None

    def set_custom_namelists(
        self,
        custom_dr_first_names: Set = None,
        custom_dr_last_names: Set = None,
        custom_patient_first_names: Set = None,
        custom_patient_last_names: Set = None,
    ):
        """Supply custom name lists for patient and doctor names when available.

        Args:
            custom_dr_first_names (Set, optional): List of known doctor first names. Defaults to None.
            custom_dr_last_names (Set, optional): List of known doctor last names. Defaults to None.
            custom_patient_first_names (Set, optional): List of known patient first names. Defaults to None.
            custom_patient_last_names (Set, optional): List of known patient last names. Defaults to None.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        # check for nan values in custom namelists
        self.finder_custom_dr_first_names = self._remove_NaN(
            custom_dr_first_names
        )
        self.finder_custom_dr_last_names = self._remove_NaN(
            custom_dr_last_names
        )
        self.finder_custom_patient_first_names = self._remove_NaN(
            custom_patient_first_names
        )
        self.finder_custom_patient_last_names = self._remove_NaN(
            custom_patient_last_names
        )
        return self

    def set_max_field_size(self, max_field_size: Union[Literal["auto"], int] = 131072):
        """Avoids _csv.Error: field larger than field limit.

        Args:
            max_field_size (Union[Literal['auto'], int], optional): Maximum field size allowed by the parser. Defaults to 131072.

        Raises:
            ValueError: Could not determine the field size limit automatically.
            ValueError: Provided field_size_limit was neither 'auto' nor int.

        Returns:
            pyDeidBuilder: Instance of the pyDeidBuilder class, allowing method chaining.
        """
        if max_field_size == "auto":
            max_int = sys.maxsize
            decrement = max_int // 2
            while decrement > 0:
                try:
                    csv.field_size_limit(max_int)
                    return self
                except OverflowError:
                    max_int -= decrement
                    decrement = decrement // 2
            raise ValueError("Unable to set CSV field size limit")
        elif max_field_size == 131072:
            # Default value, no need to change
            return self
        elif isinstance(max_field_size, int):
            csv.field_size_limit(max_field_size)
            return self
        else:
            raise ValueError("max_field_size must be 'auto', 131072, or an integer")

    def build(self):
        """Build a Deidentifier object.

        Returns:
            Deidentifier: An object that is designed to de-identify a file given the configuration specified by the pyDeidBuilder.
        """

        if self.original_file:
            self._set_file_defaults()

        # in case .replace_phi() is not called
        if self.deid.regex_replace and not self.replacer:
            self.replace_phi()

        self.finder = PHIFinder(config=PHIFinder.Config(
            phi_types = self.phi_types,
            custom_regexes = self.finder_custom_regexes,
            two_digit_threshold = self.finder_two_digit_threshold,
            valid_year_low = self.finder_valid_year_low,
            valid_year_high = self.finder_valid_year_high,
            custom_dr_first_names = self.finder_custom_dr_first_names,
            custom_dr_last_names = self.finder_custom_dr_last_names,
            custom_patient_first_names = self.finder_custom_patient_first_names,
            custom_patient_last_names = self.finder_custom_patient_last_names,
            ner_model = self.ner_model,
        ))

        if self.replacer is not None:
            self.replacer.load_phi_types(self.finder)

        handler = PHIHandler(self.deid.regex_replace, mll_rows=self.mll_rows)
        handler.set_finder(self.finder)
        handler.set_pruner(self.pruner)

        if self.replacer is not None:
            handler.set_replacer(self.replacer)

        self.deid.handler = handler

        return self.deid
