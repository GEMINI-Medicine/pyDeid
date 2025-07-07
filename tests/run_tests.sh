#!/bin/bash

#Having pydeid as your current directory
# install pytest with pip install pytest
# Dont forget to set executable permissions to this file: use chmod +x ./tests/run_tests.sh
# Then run this file with ./tests/run_tests.sh <username without unity\>

if ! command -v pytest &> /dev/null; then
        echo "pytest is not installed. Installing..."
        pip install pytest
else
    echo "pytest is already installed."
fi

USER="$1"
pytest -v "/mnt/nfs/home/$USER/pydeid/tests/test_pydeid.py" 
pytest -v "/mnt/nfs/home/$USER/pydeid/tests/test_deid_string.py" 
#!/bin/bash

#Having pydeid as your current directory
# install pytest with pip install pytest
# Dont forget to set executable permissions to this file: use chmod +x ./tests/run_tests.sh
# Then run this file with ./tests/run_tests.sh <username without unity\>

if ! command -v pytest &> /dev/null; then
        echo "pytest is not installed. Installing..."
        pip install pytest
else
    echo "pytest is already installed."
fi

USER="$1"
pytest -v "/mnt/nfs/home/$USER/pydeid/tests/test_pydeid.py" 
pytest -v "/mnt/nfs/home/$USER/pydeid/tests/test_deid_string.py" 