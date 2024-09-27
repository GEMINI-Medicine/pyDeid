import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .phi_types.names import name_first_pass
from .process_note.find_PHI import find_phi
from .process_note.prune_PHI import prune_phi
from .process_note.replace_PHI import replace_phi
from .phi_types.dates import Date, Time

# Import the create_ner_xml function from the previous example
from .phi_types.utils import phi_to_xml

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from xml.dom import minidom

import re


def pyDeid_n2c2(input_dir, output_dir):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all XML files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".xml"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # Parse the input XML file
            tree = ET.parse(input_path)
            root = tree.getroot()

            # Find the TEXT element
            text_elem = root.find(".//TEXT")
            if text_elem is not None and text_elem.text:
                # Extract the text content, removing CDATA wrapper if present
                text = text_elem.text
                if text.startswith("<![CDATA[") and text.endswith("]]>"):
                    text = text[9:-3]

                # Apply the manipulate_string function
                try:
                    phi = name_first_pass(text)
                    find_phi(text, phi)
                    prune_phi(text, phi)

                    surrogates, new_note = replace_phi(
                        text, phi, return_surrogates=True
                        )

                    surrogates = map_phi_types(surrogates)
                    
                except:
                    surrogates = pd.DataFrame(columns = ['phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types'])
                    new_note = text

                # Create the new XML content
                new_xml_content = phi_to_xml(new_note, surrogates)

                # Write the new XML content to the output file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(new_xml_content)

                print(f"Processed {filename} and saved to {output_path}")
            else:
                print(f"No TEXT element found in {filename}")


def map_phi_types(dict_list):
    """
    Apply find_phi_type function to the 'types' key in each dictionary of the input list.
    
    :param dict_list: List of dictionaries, each containing a 'types' key with a list of strings
    :return: New list of dictionaries with updated 'types' values
    """
    def update_types(d):
        if 'types' in d and isinstance(d['types'], list):
            d['types'] = find_phi_type(d['types'])
        return d
    
    return [update_types(d.copy()) for d in dict_list]


def phi_to_xml(text, entities):
    # Create the root element
    root = ET.Element("NGRID_deId")
    
    # Add the TEXT element with CDATA
    text_elem = ET.SubElement(root, "TEXT")
    text_elem.text = f"<![CDATA[{text}]]>"
    
    # Create the TAGS element
    tags_elem = ET.SubElement(root, "TAGS")
    
    # Add each entity as a tag
    for i, entity in enumerate(entities):
        

        entity_elem = ET.SubElement(tags_elem, entity['type'].upper())
        entity_elem.set("id", f"P{i}")
        entity_elem.set("start", str(entity['start']))
        entity_elem.set("end", str(entity['end']))
        entity_elem.set("TYPE", entity['type'].upper())
        entity_elem.set("comment", "")
    
    # Convert to a string and pretty print
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
