from distutils.core import setup
import os

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements.txt
requirements_file = 'requirements.txt'
if os.path.exists(requirements_file):
    with open(requirements_file, 'r') as req_file:
        install_requires = req_file.read().splitlines()
else:
    raise RuntimeError(f'{requirements_file} not found')

setup(
    name='pyDeid',
    packages=['pyDeid', 'pyDeid.phi_types', 'pyDeid.process_note'],
    package_dir={'pyDeid': 'src/pyDeid'},
    package_data={'pyDeid': ['wordlists/*.txt']},
    version='1.0.1',
    license='MIT',
    description='Replaces personal health information in free text.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Vaakesan Sundrelingam',
    author_email='vaakesan.sundrelingam@unityhealth.to',
    maintainer='GEMINI',
    maintainer_email='gemini.data@unityhealth.to',
    keywords=['De-identification', 'PHI'],
    python_requires=">=3.8",
    install_requires=install_requires,  # <-- include this
)
