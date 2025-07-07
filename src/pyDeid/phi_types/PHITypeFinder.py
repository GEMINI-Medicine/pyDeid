from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Dict, List

PHI = namedtuple("PHI", ["start", "end", "phi"])
PHIDict = Dict[str, List[str]]


class PHITypeFinder(ABC):
    """
    Abstract base class for Protected Health Information (PHI) finders.
    """

    def __init__(self):
        self.phis = {}
        self.note = ''

    def set_note(self, new_note:str)-> None:
        self.note = new_note
        
    def set_phis(self, new_phis) -> None:
        self.phis = new_phis

    @abstractmethod
    def find(self) -> PHIDict:
        """
        Find phand return all occurrences of the PHI type in the given text.
        """
        pass