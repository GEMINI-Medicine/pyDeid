import re
from ..phi_types.utils import PHI, is_common, is_ambig, is_type, add_type

def prune_phi(raw_text, phi):
    phi_keys = sorted(phi.keys(), key = lambda x: x.start)
    
    # check ambiguous type phi
    for i in range(len(phi_keys)):
        current_key = phi_keys[i]

        if i != 0:
            prev_key = phi_keys[i-1]

            if (
                (is_type(prev_key, 'Name', 1, phi) and is_type(current_key, 'Name', 1, phi))
                and not is_common(current_key.phi) and not is_common(prev_key.phi) 
                and not re.search(r'\.', prev_key.phi)
                and not ((current_key.end - prev_key.start) < 3)
                ):

                if (
                    (is_ambig(current_key, phi) and is_ambig(prev_key, phi) and is_type(prev_key, 'First Name', 1, phi) and is_type(current_key, 'Last Name', 1, phi)) or
                    (not is_ambig(current_key, phi) and is_ambig(prev_key, phi) and is_type(prev_key, 'First Name', 1, phi) and is_type(current_key, 'Last Name', 1, phi)) or
                    (is_ambig(current_key, phi) and not is_ambig(prev_key, phi) and is_type(prev_key, 'First Name', 1, phi) and is_type(current_key, 'Last Name', 1, phi))
                    ):
                    add_type(current_key, 'Last Name (probably)', phi)
                    add_type(prev_key, 'First Name (probably)', phi)

                if (
                    (not is_ambig(current_key, phi) and is_ambig(prev_key, phi) and is_type(current_key, "First Name", 1, phi) and is_type(prev_key, "Last Name", 1, phi)) or
                    (is_ambig(current_key, phi) and not is_ambig(prev_key, phi) and is_type(current_key, "First Name", 1, phi) and is_type(prev_key, "Last Name", 1, phi))
                    ):
                    add_type(current_key, 'First Name (probably)', phi)
                    add_type(prev_key, 'Last Name (probably)', phi)

    # loop once to remove ambiguous only phi
    for i in range(len(phi_keys)):
        current_key = phi_keys[i]

        if is_ambig(current_key, phi): # remove ambiguous
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
