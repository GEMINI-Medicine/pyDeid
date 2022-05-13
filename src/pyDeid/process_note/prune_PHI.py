import sys
sys.path.append('../')

import re
from phi_types.utils import PHI

def prune_phi(raw_text, phi):
    phi_keys = sorted(phi.keys(), key = lambda x: x.start)
    
    # loop once to remove ambiguous only phi
    for i in range(len(phi_keys)):
        current_key = phi_keys[i]
        
        if all(re.search('ambig', val) for val in phi[current_key]): # remove ambiguous
            del phi[current_key]
            
    phi_keys = sorted(phi.keys(), key = lambda x: x.start)
    bad_keys = []
    
    # loop again to remove overlapping phi
    for i in range(len(phi_keys)):
        current_key = phi_keys[i]
        
        if i != 0:
            previous_key = phi_keys[i-1]
                
            previous_start = phi_keys[i-1].start
            previous_end = phi_keys[i-1].end
            current_start = phi_keys[i].start
            current_end = phi_keys[i].end
            
            if current_start >= previous_start and current_end <= previous_end:
                bad_keys.append(current_key)
            
            elif current_start > previous_start and current_start < previous_end and current_end > previous_end:

                if 'Day Month' in phi[previous_key] and 'Day Month Year' in phi[current_key]:
                    bad_keys.append(previous_key)
                    
                elif 'Month Day' in phi[previous_key] and 'Month Day Year' in phi[current_key]:
                    bad_keys.append(previous_key)
                    
                else:
                    new_key = PHI(previous_start, current_end, raw_text[previous_start:current_end])
                    new_val = phi[current_key] + phi[previous_key]

                    bad_keys.append(current_key)
                    bad_keys.append(previous_key)
                    phi[new_key] = new_val
            
            elif current_start <= previous_start and current_end >= previous_end:
                bad_keys.append(previous_key)
            
            # if found PHI is part of a medical phrase, ignore it to reduce false positives
            elif any(re.search('MedicalPhrase', val) for val in phi[current_key]) and (current_start <= previous_start and current_end >= previous_end):
                bad_keys.append(previous_key)
                bad_keys.append(current_key)
                
            elif any(re.search('MedicalPhrase', val) for val in phi[previous_key]) and (current_start > previous_start and current_start < previous_end and current_end > previous_end):
                bad_keys.append(previous_key)
                bad_keys.append(current_key)
    
    for key in phi_keys:
        if any(re.search('MedicalPhrase', val) for val in phi[key]):
            bad_keys.append(key)
                
    for key in bad_keys:
        phi.pop(key, None) # check this

    return phi
