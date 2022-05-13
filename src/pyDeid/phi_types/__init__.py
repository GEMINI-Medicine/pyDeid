from .addresses import *
from .contact_info import *
from .dates import *
from .IDs import *
from .names import *
from .utils import *
from os import path

__all__ = ['addresses', 'contact_info', 'dates', 'IDs', 'names', 'utils']
wordlists = path.join(path.dirname(__file__), '..', 'wordlists')