from phi_types.names import name_first_pass
from find_PHI import find_phi
from prune_PHI import prune_phi
from replace_PHI import replace_phi

if __name__ == "__main__":
    raw_text = "Dr. Amol Verma and Dr. Fahad Razak are the GEMINI Co-Leads."

    phi = name_first_pass(raw_text)
    find_phi(raw_text, phi)
    prune_phi(raw_text, phi)
    replacements, res = replace_phi(raw_text, phi, return_replacements = True)

    print(res)

