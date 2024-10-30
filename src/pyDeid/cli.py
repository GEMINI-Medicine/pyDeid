from .pyDeidBuilder import pyDeidBuilder
import os
import argparse
from .phi_types.utils import CustomRegex
from typing import *
import importlib.util


if __name__ == "__main__":

    def str_to_bool(value):
        if value.lower() == "true":
            return True
        else:
            return False

    parser = argparse.ArgumentParser(
        description="PyDeid tool to sensitize Personal Health Information"
    )

    parser.add_argument(
        "--original_file",
        type=str,
        required=True,
        help="The input file that contains the puzzles.",
    )
    parser.add_argument(
        "--encounter_id_varname",
        type=str,
        required=False,
        default="genc_id",
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--note_varname",
        type=str,
        required=False,
        default="note_text",
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--note_id_varname",
        type=str,
        required=False,
        default=None,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--enable_replace",
        type=str_to_bool,
        default=True,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--return_surrogates",
        type=str_to_bool,
        default=True,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--max_field_size",
        type=int,
        default=131072,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--file_encoding",
        type=str,
        default="utf-8",
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--read_error_handling",
        type=str,
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--new_file",
        type=str,
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )

    parser.add_argument(
        "--phi_output_file",
        type=str,
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--phi_output_file_type",
        type=str,
        choices=["json", "csv"],
        default="csv",
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--mll_file",
        type=str,
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    
    parser.add_argument(
        "--named_entity_recognition",
        type=str_to_bool,
        default=False,
        required=False,
        help="The output file that contains the solution.",
    )

    parser.add_argument(
        "--two_digit_threshold",
        type=int,
        default=30,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--valid_year_low",
        type=int,
        default=1900,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--valid_year_high",
        type=int,
        default=2050,
        required=False,
        help="The output file that contains the solution.",
    )

    parser.add_argument(
        "--custom_dr_first_names",
        type=lambda s: set(s.split(',')),
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
    "--custom_dr_last_names",
    type=lambda s: set(s.split(',')),
    default=None,
    required=False,
    help="Comma-separated list of last names.",
    )

    parser.add_argument(
        "--custom_patient_first_names",
        type=lambda s: set(s.split(',')),
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--custom_patient_last_names",
        type=lambda s: set(s.split(',')),
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--verbose",
        type=str_to_bool,
        default=True,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--types",
        type=str,
        nargs="*",
        default=[
            "names",
            "dates",
            "sin",
            "ohip",
            "mrn",
            "locations",
            "hospitals",
            "contact",
        ],
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--custom_regexes",
        type=str,
        nargs="+",
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )

    parser.add_argument(
        "--cr_surrogate_file",
        type=str,
        default=None,
        required=False,
        help="The output file that contains the solution.",
    )
    parser.add_argument(
        "--encounter_id_varname_mll",
        type=str,
        default='genc_id',
        required=False,
        help="The output file that contains the solution.",
    )
    args = parser.parse_args()
   
    file_path = os.path.expanduser(args.original_file)
    if args.cr_surrogate_file and args.custom_regexes:  # this is a python file
        file_path_custom_surrogates = os.path.expanduser(args.cr_surrogate_file)
  
    builder = (
        pyDeidBuilder()
        .replace_phi(args.enable_replace, args.return_surrogates)
        .set_input_file(
            original_file=file_path,
            encounter_id_varname=args.encounter_id_varname,
            note_varname=args.note_varname,
            note_id_varname=args.note_id_varname,
            max_field_size=args.max_field_size,
            file_encoding=args.file_encoding,
            read_error_handling=args.read_error_handling,
        )
        .set_phi_types(args.types)
    )

    if args.new_file:
        builder.set_deid_output_file(args.new_file)
    else:
        builder.set_deid_output_file()

    if args.phi_output_file:
        builder.set_phi_output_file(args.phi_output_file, args.phi_output_file_type)
    else:
        builder.set_phi_output_file()

    if (
        args.custom_dr_first_names
        or args.custom_dr_last_names
        or args.custom_patient_first_names
        or args.custom_patient_last_names
    ):
        builder.set_custom_namelists(
            args.custom_dr_first_names,
            args.custom_dr_last_names,
            args.custom_patient_first_names,
            args.custom_patient_last_names,
        )

    if args.named_entity_recognition:
        from spacy import load

        nlp = load("en_core_web_sm")
        builder.set_ner_pipeline(nlp)

    if args.mll_file:
        mll_file = os.path.expanduser(args.mll_file)
        builder.set_mll(
            mll_file,
            args.encounter_id_varname_mll,
            args.file_encoding,
            args.read_error_handling,
        )

    if args.cr_surrogate_file and args.custom_regexes:
        spec = importlib.util.spec_from_file_location(
            "module.name", file_path_custom_surrogates
        )
        surrogate_module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(surrogate_module)

        for regex_str in args.custom_regexes:
            parts = regex_str.split(",")
       
            # Extract the components
            pattern = parts[0].strip()
            phi_type = parts[1].strip()
            surrogate_builder_fn = parts[2].strip()  # This is the function name
            arguments = [
                arg.strip("'") for arg in parts[3:]
            ]  # Remaining parts are arguments
            
            # now surrogate_builder_fn could be a lambda or not
            if surrogate_builder_fn.strip().startswith(
                "lambda"
            ):  # convert a this strign to its lambda equivalent

                function = eval(surrogate_builder_fn)

            else:  # if a function is a proper user defined function
                function_name = surrogate_builder_fn.strip()
                if hasattr(surrogate_module, function_name):
                    function = getattr(surrogate_module, function_name)

            # Now call the function with the arguments
            # eval here ensures the args string representations are converted correctly
            evaluated_args = []
            for arg in arguments:
                try:
                    evaluated_args.append(eval(arg))
                except:
                    evaluated_args.append(arg)

            builder.set_custom_regex(pattern, phi_type, function, evaluated_args)

    deid = builder.set_valid_years(
        args.two_digit_threshold, args.valid_year_low, args.valid_year_high
    ).build()

    deid.run(args.verbose)
