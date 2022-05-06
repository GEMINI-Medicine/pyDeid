# `PyDeid`

## 1 Objective

`PyDeid` is a Python-based refactor of the [Physionet Perl-based De-identification Software](https://physionet.org/content/deid/1.1/), which uses regular expressions and lookup dictionaries to identify and replace PHI in free text.

The purpose was to create a faster, and easier to use process to de-identify large volumes of (large) clinical notes. `PyDeid` is at least 6.3x faster than the perl-based software, and requires no pre or post processing. Additionally, surrogate replacement is more transparent.

## 2 Getting Started

`pyDeid` has no dependencies and only requires `Python3`.

Example `pyDeid` call (please see docstring for parameter definitions):

```
pyDeid(
    original_file = 'test.csv', 
    new_file = 'test_deid.csv', 
    phi_output_file = 'test_phi.csv', 
    note_varname = 'note_text', 
    encounter_id_varname = 'genc_id', 
    note_id_varname = 'note_id',
    mode = 'performance'
    )
```

The `original_file` is provided in the structure of a dataframe and saved in CSV format. `pyDeid` writes a de-identified version of the dataframe to `new_file` and writes locations of found PHI (as well as their replacements) to `phi_output_file`. It is recommended to use `mode = 'performance'` if a "large" number of notes is being processed at once (please see the docstring for details).