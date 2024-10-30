import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .phi_types.names import name_first_pass
from .process_note.find_PHI import find_phi
from .process_note.prune_PHI import prune_phi
from .process_note.replace_PHI import replace_phi
from .phi_types.dates import Date, Time

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from xml.dom import minidom

import re
import pandas as pd

from typing import List


def pyDeid_n2c2(
    input_dir,
    output_dir,
    types: List[str] = ["names", "dates", "ssn", "mrn", "locations", "zip", "contact"],
):
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
                    find_phi(text, phi, custom_regexes={})
                    prune_phi(text, phi)

                    surrogates, new_note = replace_phi(
                        text, phi, return_surrogates=True
                    )

                    surrogates = map_phi_types(surrogates)

                except:
                    surrogates = (
                        []
                    )  # pd.DataFrame(columns = ['phi_start', 'phi_end', 'phi', 'surrogate_start', 'surrogate_end', 'surrogate', 'types'])
                    new_note = text

                # Create the new XML content
                new_xml_content = phi_to_xml(text, surrogates)

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
        if "types" in d and isinstance(d["types"], list):
            d["types"] = find_phi_type(d["types"])
        return d

    return [update_types(d.copy()) for d in dict_list]


def phi_to_xml(text, entities):
    # Create the root element
    root = ET.Element("NGRID_deId")

    # Add the TEXT element with CDATA
    text_elem = ET.SubElement(root, "TEXT")
    text_elem.text = text

    # Create the TAGS element
    tags_elem = ET.SubElement(root, "TAGS")

    # Add each entity as a tag
    if entities:
        for i, entity in enumerate(entities):
            try:
                entity_elem = ET.SubElement(tags_elem, entity["types"].upper())
                entity_elem.set("id", f"P{i}")
                entity_elem.set("start", str(entity["phi_start"]))
                entity_elem.set("end", str(entity["phi_end"]))
                entity_elem.set("TYPE", entity["types"].upper())
                entity_elem.set("comment", "")
            except:
                import ipdb

                ipdb.set_trace()

    # Convert to a string and pretty print
    rough_string = ET.tostring(root, "unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def find_phi_type(types):
    """
    Match a list of types against predefined patterns and return the corresponding output.

    :param types: List of strings representing types to match
    :return: The output string corresponding to the first matching pattern, or "OTHER" if no match
    """
    patterns = [
        (r"Holiday", "HOLIDAY"),
        (r"Time", "TIME"),
        (r"Day|Month|Year", "DATE"),
        (r"(First|Last\s*)?Name(\sPrefix)?", "NAME"),
        (r"Address|Street|City|State|Zip|Location", "LOCATION"),
        (r"Email Address", "EMAIL"),
        (r"Telephone/Fax", "CONTACT"),
        (r"OHIP", "ID"),
        (r"SIN", "ID"),
        (r"MRN", "ID"),
    ]

    # Join all types into one string, separated by spaces
    combined_types = " ".join(types)

    # Check each pattern in the order they are defined
    for pattern, output in patterns:
        if re.search(pattern, combined_types, re.IGNORECASE):
            return output

    # If no match found
    return "OTHER"


def split_multi_word_tags(input_dir, output_dir):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    def smart_split(text):
        # Split on word boundaries, keeping track of positions
        words_with_positions = []
        for match in re.finditer(r"\b\w+\b", text):
            words_with_positions.append((match.group(), match.start(), match.end()))
        return words_with_positions

    # Process each XML file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".xml"):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)

            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()

            # Find all tags that need to be split (assuming all caps tag names are entities)
            tags_to_split = root.findall(".//TAGS/*[@text]")

            for tag in tags_to_split:
                text = tag.get("text")
                start = int(tag.get("start"))
                tag_type = tag.tag

                # Split the text into words
                words_with_positions = smart_split(text)

                if len(words_with_positions) > 1 and tag_type == "NAME":
                    root.find(".//TAGS").remove(tag)

                    # add new tags for each word
                    for i, (word, word_start, word_end) in enumerate(
                        words_with_positions
                    ):
                        new_tag = ET.Element(tag_type)
                        new_tag.set("id", f"{tag.get('id')}_{i}")
                        new_tag.set("start", str(start + word_start))
                        new_tag.set("end", str(start + word_end))
                        new_tag.set("text", word)
                        new_tag.set("TYPE", tag.get("TYPE"))
                        new_tag.set("comment", tag.get("comment", ""))

                        root.find(".//TAGS").append(new_tag)

            # Convert the ElementTree to a string
            rough_string = ET.tostring(root, "utf-8")

            # Use minidom to prettify the XML
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Write the prettified XML to the output file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(pretty_xml)

            print(f"Processed {input_file} and saved results to {output_file}")

    print(f"Finished processing all XML files from {input_dir}")
