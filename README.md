# `PyDeid`

## 1 Objective

`PyDeid` is a Python-based refactor of the [Physionet Perl-based De-identification Software](https://physionet.org/content/deid/1.1/), which uses regular expressions and lookup dictionaries to identify and replace PHI in free text.

The purpose was to create a faster, and easier to use process to de-identify large volumes of (large) clinical notes. `PyDeid` is at least 6.3x faster than the perl-based software, and requires no pre or post processing. Additionally, surrogate replacement is more transparent.

## 2 Getting Started

### 2.1 Installation and Setup

`pyDeid` has no external dependencies and only requires `Python3`. However, in order to install the package using `pip` as outlined below, `setuptools>=42` is required.

If you have downloaded (and unzipped) this package to a local folder `/path/to/package/` simply install via `pip3 install --user /path/to/package/`. Note that if you are connected through VPN to your institution's network you may need to run the command with the following options: `pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user /path/to/package/`.

To now import from this package, you may need to add the install location (found via `pip show pyDeid`) to your `$PYTHONPATH` so `Python` knows where to look for it:

```
import sys
sys.path.append('/path/from/pip_show_pydeid/')
```

### 2.2 Running De-identification

Simply test using:

```
from pyDeid import deid_string

deid_string('Justin Bieber is from Stratford')
```

Or to deidentify an entire `csv` file:

```
from pyDeid import pyDeid

pyDeid(
    original_file = '/path/to/test.csv', 
    new_file = '/future/path/to/test_deid.csv', 
    phi_output_file = '/future/path/to/test_phi.csv', 
    note_varname = 'note_text', 
    encounter_id_varname = 'genc_id', 
    note_id_varname = 'note_id',
    mode = 'performance'
    )
```

`test.csv` may look like this (and is provided under the `tests/` directory of the package):

```
genc_id,note_id,note_text
1,Record 1,John Smith was born on March 01 1994
2,Record 2,"GEMINI is located at 30 Bond St, Toronto, ON, M5B 1W8"
3,Record 3,"Dr Amol Verma and Dr. Fahad Razak are GEMINI co-leads.
"
4,Record 4,Test MRN: 011-0111
5,Record 5,"14 Jun 06, 2017"
```

The `original_file` is provided in the structure of a dataframe and saved in CSV format. `pyDeid` writes a de-identified version of the dataframe to `new_file` and writes locations of found PHI (as well as their replacements) to `phi_output_file`. It is recommended to use `mode = 'performance'` if a "large" number of notes is being processed at once (please see the docstring for details).
