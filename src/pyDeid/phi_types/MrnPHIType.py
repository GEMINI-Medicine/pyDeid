from typing import Dict, List
import re
from .PHITypeFinder import PHITypeFinder, PHI, PHIDict


class MrnPHIType(PHITypeFinder):
    """
    Implementation of PHIType for Medical Record Numbers (MRN).
    """

    def find(self, text: str) -> PHIDict:
        phi = {}

        for m in re.finditer(
            r"((mrn|medical record|hospital number)( *)(number|num|no|#)?( *)[\)\#\:\-\=\s\.]?( *)(\t*)( *)[a-zA-Z]*?((\d+)[\/\-\:]?(\d+)?))[a-zA-Z]*?",
            text,
            re.IGNORECASE,
        ):
            phi.setdefault(PHI(m.start(9), m.end(9), m.group(9)), []).append("MRN")

        return phi

    @property
    def name(self):
        return "MRN"
