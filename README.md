# `PyDeid`

See [read the docs](https://gemini-medicine.github.io/pyDeid/index.html) for extensive examples and a detailed feature breakdown.

## 1 Objective

`PyDeid` is a Python-based refactor of the [Physionet Perl-based De-identification Software](https://physionet.org/content/deid/1.1/), which uses regular expressions and lookup dictionaries to identify and replace PHI in free text.

The purpose was to create a faster, and easier to use tool to de-identify large volumes of (large) clinical notes. `PyDeid` is up to 5.4x faster than the perl-based software, and requires no pre or post processing. Additional enhancements include the ability to re-identify text, supply custom patterns, and supply custom doctor and patient namelists without having to save them to persistent storage, and incorporate `spaCy` NER pipelines.

## 2 Local Installation and Setup

If you have downloaded (and unzipped) this package to a local folder `/path/to/package/` simply install via `pip3 install --user /path/to/package/`. 

Note that if you are connected through VPN to your institution's network you may need to run the command with the following options: `pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user /path/to/package/`.

Dependencies can be installed with `pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r /path/to/requirements.txt/`.

> *Note*: You may encounter a deprecation warning about building local packages in place without first copying to a temporary directory in a future version of `pip`. Note that `pyDeid` has been tested with this change and the installation will continue to work when this behaviour becomes the default.

To now import from this package, you may need to add the install location (found via `pip show pyDeid`) to your `$PYTHONPATH` so `Python` knows where to look for it:

```
import sys
sys.path.append('/path/from/pip_show_pydeid/')
```

Test your installation by running the following:

```
from pyDeid import deid_string
deid_string('Justin Bieber was born on March 1st, 1994.')
```

## 3 CSV File De-identification

`pyDeid` only requires that the free text data be stored in a CSV file with named column headers. 

Specifying a column of encounter IDs (and optionally note IDs) with `encounter_id_varname` and `note_id_varname` respectively is relevant in only to assign the found PHI to a particular encounter and note identifier for further analysis.

There may be multiple columns containing free text, but `PyDeid` will only de-identify a single column at a time. In order to de-identify multiple columns of text, make multiple passes of the same file with `pyDeid` on the same file.

Consider a `test.csv` that looks like this (and is provided under the `tests/` directory of the package):

```
genc_id,note_id,note_text
1,Record 1,Justin Bieber was born on March 1st, 1994.
2,Record 2,"St.Michael's hospital is located at 30 Bond St, Toronto, ON, M5B 1W8
"
3,Record 3,Test MRN: 011-0111
```

Note that each note (in the `note_text` field) is uniquely identified by a `genc_id` and a `note_id`.

To de-identify this file with default settings, simply supply:

* The filename as `original_file`
* The name of the column containing the note as `note_varname`
* The name of the encounter identifying column as `encounter_id_varname`
* And the name of the note (within encounter) identifying column as `note_id_varname`

```
from pyDeid import pyDeid

pyDeid(
    original_file = ‘test.csv’, 
    note_varname = ‘note_text’, 
    encounter_id_varname = ‘genc_id’,
    note_id_varname = 'note_id'
)
```

## 4 Additional Arguments

Additional settings are described in the [API documentation](https://gemini-medicine.github.io/pyDeid/api/index.html), and covered extensively in the [tutorial notebooks](https://gemini-medicine.github.io/pyDeid/tutorials/index.html). 

Some arguments are described below:

* A file name for the de-identified csv can be supplied with `new_file`, or will take the form `<original file name>__DE-IDENTIFIED.csv`.
* The PHI output can be stored as a `json` or `csv` file (specified by the `phi_output_file_type` parameter), and optionally the file name can be provided using the `phi_output_file` parameter. The `json` data structure is more efficient on space, but is much heavier on memory. The `csv` data structure is inefficient on space but much lighter on memory.
* There is a `verbose` mode which displays a progress bar and prints speed diagnostics at the end of the run.

One of the main advantages of `PyDeid` over `Physionet De-identification Software v1.1` is the ability to supply a set of doctor and patient first and last names to be recognized as PHI, without having to write this sensitive information to persistent storage. These custom blacklists can be read into a python Set and supplied to `PyDeid` through the `custom_dr_first_names`, `custom_dr_last_names`, `custom_patient_first_names`, and `custom_patient_last_names` parameters for better recall and precision.

Additionally, `PyDeid` allows custom regexes for site-specific PHI to be supplied through keyword arguments. Simply supply a named regex argument to `PyDeid` or `deid_string` like so:

```
deid_string(
    ‘The site-specific identifier at your hospital is NH12345’, 
    site_identifier = ‘NH\d{5}’
)
```

## 5 Additional Functions

`deid_string` is a simplified function to de-identify a single string at a time which can be used for debugging, or written into a custom wrapper if `PyDeid` fails to meet the requirements of the problem. It can optionally be combined with the `reid_string` function which takes the output of `deid_string` and returns the input to `deid_string`.

```
from pyDeid import reid_string

original_string = 'Justin Bieber was born in Stratford on March 1st, 1994.'

phi, new_string = deid_string(original_string)
reidentified_string = reid_string(new_string, phi)

print(original_string == reidentified_string)
```

Additionally, the de-identification results can be visualized with `spaCy`.

```
from pyDeid import display_deid

display_deid(original_string, phi)
```

## 6 Reporting Issues

Please report any bugs or feature requests as issues to the `PyDeid` repository. For any bugs, please supply a minimal reproducible example to guarantee a quicker resolution.