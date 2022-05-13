import re
from .utils import add_type, PHI


def sin(x, phi):
    for m in re.finditer(r'\b(\d{3}([- \/]?)\d{3}\2\d{3})\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'SIN', phi)


def ohip(x, phi):
    for m in re.finditer(r'\b\d{4}[- \/]?\d{3}[- \/]?\d{3}[- \/]?([a-zA-Z]?[a-zA-Z]?)\b', x):
        add_type(PHI(m.start(), m.end(), m.group()), 'OHIP', phi) 


def mrn(x, phi):
    for m in re.finditer(r'\b((mrn|medical record)( *)(number|num|no)?( *)[\)\#\:\-\=\s\.]?( *)(\t*)( *)((\d+)[\/\-\:]?(\d+)?))\b', x, re.IGNORECASE):
        add_type(PHI(m.start(9), m.end(9), m.group(9)), 'MRN', phi)
