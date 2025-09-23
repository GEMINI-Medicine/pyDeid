from distutils.core import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
  name='pyDeid',
  packages=['pyDeid', 'pyDeid.phi_types', 'pyDeid.process_note'],
  package_dir={'pyDeid': 'src/pyDeid'},
  package_data={'pyDeid': ['wordlists/*.txt']},
  version='1.0.0',
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
)
