# `PyDeid`

## 1 Objective

`PyDeid` is a Python-based refactor of the [Physionet Perl-based De-identification Software](https://physionet.org/content/deid/1.1/), which uses regular expressions and lookup dictionaries to identify and replace PHI in free text.

The purpose was to create a faster, and easier to use process to de-identify large volumes of (large) clinical notes. `PyDeid` is at least 6.3x faster than the perl-based software, and requires no pre or post processing. Additional enhancements include the ability to re-identify text, supply custom patterns, and supply custom doctor and patient namelists without having to save them to persistent storage.

## 2 Local Installation and Setup

If you have downloaded (and unzipped) this package to a local folder `/path/to/package/` simply install via `pip3 install --user /path/to/package/`. 

Note that if you are connected through VPN to your institution's network you may need to run the command with the following options: `pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user /path/to/package/`.

To now import from this package, you may need to add the install location (found via `pip show pyDeid`) to your `$PYTHONPATH` so `Python` knows where to look for it:

```
import sys
sys.path.append('/path/from/pip_show_pydeid/')
```

Test your installation by running the following:

```
from pyDeid import deid_string
deid_string('Justin Bieber is from Stratford')
```

## 4 AIO Installation and Setup

Almost all de-identification is done on AIO. Therefore it is important to set up `pyDeid` on AIO. This process is somewhat more involved than the local setup:

1. Clone the `git` repository to a path (for example `/path/to/pydeid`) using the following command:

```git clone git@gitlab.smh.smhroot.net:geminidata/pydeid.git```

2. Navigate to the folder to which it was cloned (for example `/path/to/pydeid`) and run the following command to install `pyDeid`:'

```pip3 install pydeid```

3. Now you may use `pyDeid` on AIO through the command line. To do this, it is recommended to create a virtual environment:
    a. To create a virtual environment named example_environment (you may name this anything you’d like), run:

    ```conda create –n example_environment```

    b. Activate the environment using:

    ```source activate example_environment.```

    c. Now we are in the virtual environment. In the environment, run:
    
    ```conda install pip``` (we will be using `pip` to install `pydeid`).

    d.Once `pip` is installed run:
    
    ```echo $CONDA_PREFIX/bin/pip install /path/to/pydeid``` (where `/path/to/pydeid` is the path to which you cloned pydeid in step 2 and `$CONDA_PREFIX` is the location of all conda virtual environments).

    e. You may also need to install pandas with:
    
    ```conda install pandas```

	And `spacy` with:

    ```conda install spacy```

4. Now you can begin de-identifying. One simple option is to use python interactively in the shell (reminder to use Ctrl+Z to exit the interactive mode). This can also be done in a [screen](https://linuxize.com/post/how-to-use-linux-screen/) session to prevent ssh session disconnections.

5. When done, simply conda deactivate to exist the session.

Another option is to run the de-identification using the Jupyter IDE (for user friendliness). However, currently this option cannot currently be used with screen.

1. Begin by setting up VSCode with AIO using [these](https://docs.google.com/document/d/1igZKvNml9KOjiuKC2jySV-dAj0-owJzai6F9DycR8sk/edit#heading=h.mllbdqszaury) instructions (only section 1 Connecting VS code to a remote server).

2. Skip section 2.

3. Follow section 3, but select the virtual environment (for example named `example_environment`) that you created above.

4. You may now use `pydeid` on AIO in a jupyter notebook!


## 5 De-identification Process

`PyDeid` only requires that the free text data be stored in a CSV file with named column headers. 

Specifying a column of encounter IDs (and optionally note IDs) with `encounter_id_varname` and `note_id_varname` respectively is relevant in only to assign the found PHI to a particular encounter and note identifier for further analysis. `encounter_id_varname` is required only when `phi_output_file_type` is `json`.

There may be multiple columns containing free text, but `PyDeid` will only de-identify a single column at a time. In order to de-identify multiple columns of text, make multiple passes of the same file with `PyDeid`.

To de-identify a file with default settings, simply do:

```
from PyDeid import PyDeid

PyDeid(
original_file = ‘test.csv’, 
note_varname = ‘note_text’, 
encounter_id_varname = ‘genc_id’
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

Additional settings are described in the function docstring. A file name for the de-identified csv can be supplied with new_file, or will take the form `<original file name>__DE-IDENTIFIED.csv`.

The PHI output can be stored as a `json` or `csv` file (specified by the `phi_output_file_type` parameter), and optionally the file name can be provided using the `phi_output_file` parameter. The `json` data structure is more efficient on space, but is much heavier on memory. The `csv` data structure is inefficient on space but much lighter on memory.

Additionally, there is a `verbose` mode which displays a progress bar and prints speed diagnostics at the end of the run.

One of the main advantages of `PyDeid` over `GEMINI De-id v2` is the ability to supply a set of doctor and patient first and last names to be recognized as PHI, without having to store this sensitive information to persistent storage. MLLs can be read into memory from zone1 into a python Set and supplied to `PyDeid` through the `custom_dr_first_names`, `custom_dr_last_names`, `custom_patient_first_names`, and `custom_patient_last_names` parameters for better recall and precision.

Additionally, `PyDeid` allows custom regexes for site-specific PHI to be supplied through keyword arguments. Simply supply a named regex argument to `PyDeid` or `deid_string` like so:

```
deid_string(
‘The site-specific identifier at Niagara is NH12345’, niagara_id = ‘NH\d{5}’
)
```

`deid_string` is a simplified function to de-identify a single string at a time which can be used for debugging, or written into a custom wrapper if `PyDeid` fails to meet the requirements of the problem. It can optionally be combined with the `reid_string` function which takes the output of `deid_string` and returns the input to `deid_string`:

```
original_string = 'Justin Bieber was born in Stratford on March 1st, 1994.'

phi, new_string = deid_string(original_string)
reidentified_string = reid_string(new_string, phi)

print(original_string == reidentified_string)
```

## 6 PyDeid Performance

`PyDeid` was validated similarly to `GEMINI De-id v2`. Precision and recall were measured on 700 annotated St Michaels admission notes. These were the same notes used to test `GEMINI De-id v2`, but were partially re-annotated due to the indexing differences between python and perl. For details on the re-annotation process, see the `Clinical Notes REValidation SOP`. The performance is given below:

| **Metric**                         | **pyDeid** | **GEMINI De-id v2** |
| ---------------------------------- | ---------- | ------------------- |
| Sensitivity/Recall: TP/(TP + FN) | 94.61%     | 94.72%              |
| Precision: TP/(TP + FP)          | 90.96%     | 90.16%              |

When MLLs are used to provide custom doctor and patient names, the performance improves:

| **Metric**                         | **Doctor Names** | **Patient Names** | **Doctor and Patient Names** |
| ---------------------------------- | ---------------- | ----------------- | ---------------------------- |
| Sensitivity/Recall: TP/(TP + FN) | 95.31%           | 96.20%            | 96.46%                       |
| Precision: TP/(TP + FP)          | 90.69%           | 90.49%            | 90.52%                       |

## 7 Reporting Issues

Please report any bugs or feature requests as issues to the `PyDeid` repository. For any bugs, please supply a minimal reproducible example to guarantee a quicker resolution.