import pandas as pd
import numpy as np
import os
from typing import List, Dict, Optional, Any
import csv
import nltk
from nltk.tokenize import word_tokenize
import string

class CSVEvaluator:
    def __init__(self) -> None:
        """
        Class which performs an evaluation of de-identification results using CSV output.
        """
        self.ground_truth_file: Optional[str] = None
        self.result_file: Optional[str] = None
        self.merged_df: Optional[pd.DataFrame] = None
        self.gt_columns: Dict[str, Optional[str]] = {}
        self.result_columns: Dict[str, str] = {}

    def add_ground_truth_file(
        self, 
        filepath: str, 
        encounter_id_varname: str = "genc_id", 
        note_id_varname: Optional[str] = None, 
        start_index_varname: str = "start", 
        end_index_varname: str = "end", 
        annotation_varname: str = "annotation",
        ignore_annotations: Optional[List[str]] = ['t', 'T']
    ) -> None:
        """
        Set the ground truth file and its column names.

        Args:
        filepath (str): Path to the ground truth CSV file.
        encounter_id_varname (str): Name of the encounter ID column.
        note_id_varname (Optional[str]): Name of the note ID column (if applicable).
        start_index_varname (str): Name of the start index column.
        end_index_varname (str): Name of the end index column.
        annotation_varname (str): Name of the annotation column.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Ground truth file not found: {filepath}")
        
        self.gt_columns = {
            'encounter_id': encounter_id_varname,
            'note_id': note_id_varname,
            'start': start_index_varname,
            'end': end_index_varname,
            'annotation': annotation_varname
        }

        CSVEvaluator.validate_and_read_file(filepath, self.gt_columns)

        ground_truth = pd.read_csv(filepath)

        if ignore_annotations:
            ground_truth['annotation'] = ground_truth['annotation']\
                .replace(ignore_annotations, np.nan)

        self.ground_truth = ground_truth

        return self

    def add_result_file(
        self, 
        filepath: str,
        encounter_id_varname: str = "encounter_id", 
        phi_start_varname: str = "phi_start", 
        phi_end_varname: str = "phi_end", 
        types_varname: str = "types"
    ) -> None:
        """
        Set the result file and its column names.

        Args:
        filepath (str): Path to the result CSV file.
        encounter_id_varname (str): Name of the encounter ID column.
        phi_start_varname (str): Name of the PHI start index column.
        phi_end_varname (str): Name of the PHI end index column.
        types_varname (str): Name of the PHI types column.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Result file not found: {filepath}")
        
        self.result_columns = {
            'encounter_id': encounter_id_varname,
            'phi_start': phi_start_varname,
            'phi_end': phi_end_varname,
            'types': types_varname
        }

        CSVEvaluator.validate_and_read_file(filepath, self.result_columns)

        self.result = pd.read_csv(filepath)

        return self

    @staticmethod
    def validate_and_read_file(filepath, columns) -> pd.DataFrame:
        """
        Validate that all required columns are present in input files.
        """
        df = pd.read_csv(filepath)
        
        missing_cols = [col for col, name in columns.items() if name and name not in df.columns]
        
        if missing_cols:
            raise ValueError(f"File is missing: {missing_cols}")

    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate the de-identification results and return metrics.

        Returns:
        Dict[str, float]: A dictionary containing 'precision', 'recall', and 'f1_score'.
        """
        self.combine_files()
        self.standardize_phi()
        return self.calculate_metrics()

    def combine_files(self) -> None:
        """
        Merge ground truth and result files, handling edge cases.
        """
        ground_truth = self.ground_truth
        deid_output = self.result

        gt_cols = self.gt_columns
        res_cols = self.result_columns

        to_analyze = pd.merge(
            ground_truth, 
            deid_output, 
            left_on=[gt_cols['encounter_id'], gt_cols['start'], gt_cols['end']],
            right_on=[res_cols['encounter_id'], res_cols['phi_start'], res_cols['phi_end']],
            how='outer', 
            indicator=True
        )

        merge_misses = pd.merge(
            ground_truth, 
            deid_output, 
            left_on=gt_cols['encounter_id'],
            right_on=res_cols['encounter_id'],
            how='inner', 
            suffixes=('_gt', '_deid')
        )
        
        merge_misses = merge_misses[
            (((merge_misses[res_cols['phi_start']] <= merge_misses[gt_cols['start']]) & 
              (merge_misses[res_cols['phi_end']] > merge_misses[gt_cols['end']])) |
             ((merge_misses[res_cols['phi_start']] < merge_misses[gt_cols['start']]) & 
              (merge_misses[res_cols['phi_end']] >= merge_misses[gt_cols['end']]))) &
            (merge_misses[gt_cols['annotation']].notna())
        ]

        res = to_analyze[
            ~to_analyze.set_index(['genc_id', 'start', 'end'])\
                .index.isin(
                    merge_misses.set_index(['genc_id', 'start', 'end']).index
                    )]

        res = res[
            ~res.set_index(['encounter_id', 'phi_start', 'phi_end'])\
                .index.isin(
                    merge_misses\
                        .set_index(
                            ['encounter_id', 'phi_start', 'phi_end']
                        ).index
                    )]

        self.merged_df = pd.concat([res, merge_misses])

    def standardize_phi(self) -> None:
        """
        Standardize PHI types in the merged DataFrame.
        """
        df = self.merged_df.rename(columns={
            self.gt_columns['annotation']: 'manual_annotation', 
            self.result_columns['types']: 'deid_annotation'
        })

        def categorize_deid(annotation: Any) -> Optional[str]:
            """Categorize de-identified annotations into standardized types."""
            if any(term in str(annotation) for term in ['Date', 'Month', 'Day', 'Year', 'Holiday']):
                return 'Date'
            elif any(term in str(annotation) for term in ['Name', 'Initials']):
                return 'Name'
            elif any(term in str(annotation) for term in ['MRN', 'Medical Record Number', 'SIN', 'OHIP']):
                return 'ID'
            elif any(term in str(annotation) for term in ['Telephone', 'Email', 'E-mail', 'Fax']):
                return 'Contact'
            elif any(term in str(annotation) for term in ['Location', 'Street', 'Postal']):
                return 'Location'
            return None

        def categorize_manual(annotation: Any) -> Optional[str]:
            """Categorize manual annotations into standardized types."""
            if annotation in ['t', 'T']:
                return 'Time'
            elif annotation in ['n', 'N']:
                return 'Name'
            elif annotation in ['d', 'D']:
                return 'Date'
            elif annotation in ['tf', 'e']:
                return 'Contact'
            elif annotation == 'i':
                return 'ID'
            elif annotation == 'l':
                return 'Location'
            return None

        df['deid_type'] = df['deid_annotation'].apply(categorize_deid)
        df['manual_type'] = df['manual_annotation'].apply(categorize_manual)

        self.merged_df = df

    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate precision, recall, and F1 score based on manual and de-identified annotations.

        Returns:
        Dict[str, float]: A dictionary containing 'precision', 'recall', and 'f1_score'.
        """
        df = self.merged_df
        
        true_positives = df[(df.manual_type.notnull()) & (df.deid_type.notnull()) & (df.manual_type == df.deid_type)].shape[0]
        false_positives = df[(df.manual_type.isnull()) & (df.deid_type.notnull())].shape[0]
        false_negatives = df[(df.manual_type.notnull()) & (df.deid_type.isnull())].shape[0]

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }


def tokenize_csv(
    input_file: str,
    output_file: str,
    encounter_id_varname: str = "genc_id",
    note_id_varname: str = "note_id",
    note_text_varname: str = "note_text"
) -> None:
    """
    Tokenize the text in a CSV file and write the results to a new CSV file.

    This function reads a CSV file, tokenizes the text in a specified column,
    and writes the tokens along with their start and end indices to a new CSV file.
    It preserves the encounter ID and note ID from the input file.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to the output CSV file to be created.
        encounter_id_varname (str, optional): Name of the column containing encounter IDs.
            Defaults to "genc_id".
        note_id_varname (str, optional): Name of the column containing note IDs.
            Defaults to "note_id".
        note_text_varname (str, optional): Name of the column containing the text to be tokenized.
            Defaults to "note_text".

    Raises:
        ValueError: If any of the specified column names are not found in the input file.

    Returns:
        None

    Note:
        - The function uses NLTK's word_tokenize for tokenization.
        - Punctuation is removed from the end of each token.
        - Empty tokens after cleaning are skipped.
        - The output CSV will have the following columns:
          [encounter_id_varname, note_id_varname, 'token', 'start', 'end']
        - The 'start' and 'end' columns represent the character indices of each token
          in the original text.

    Example:
        >>> tokenize_csv('input.csv', 'output.csv', 'encounter_id', 'note_id', 'text')
    """
    # Download the punkt tokenizer if not already downloaded
    nltk.download('punkt', quiet=True)
    
    # Define punctuation set
    punct_set = set(string.punctuation)
    
    def clean_token(token):
        # Remove punctuation only from the end of the token
        while token and token[-1] in punct_set:
            token = token[:-1]
        return token

    with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        
        # Ensure all specified columns exist in the input file
        input_columns = reader.fieldnames
        required_columns = [encounter_id_varname, note_id_varname, note_text_varname]
        if not set(required_columns).issubset(set(input_columns)):
            raise ValueError("Specified columns not found in input file")
        
        fieldnames = [encounter_id_varname, note_id_varname, 'token', 'start', 'end', 'annotation']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            encounter_id = row[encounter_id_varname]
            note_id = row[note_id_varname]
            text = row[note_text_varname]
            
            # Tokenize the original text
            tokens = word_tokenize(text)
            
            index = 0
            for token in tokens:
                clean_token_text = clean_token(token)
                
                if clean_token_text:  # Skip empty tokens
                    # Find the start index of the token in the original text
                    start_index = text.index(clean_token_text, index)
                    end_index = start_index + len(clean_token_text)
                    
                    writer.writerow({
                        encounter_id_varname: encounter_id,
                        note_id_varname: note_id,
                        'token': clean_token_text,
                        'start': start_index,
                        'end': end_index,
                        'annotation': ''
                    })
                    
                    # Update index for next search
                    index = end_index


def melt_annotations(input_file: str, output_file: str, merge_annotations: Optional[List[str]] = None) -> None:
    """
    Combine annotated tokens that are part of the same "multitoken" for specified annotations.

    This function reads a CSV file with tokenized text and annotations, and combines
    tokens that have the same annotation (from the specified list) and are close to 
    each other (less than 3 characters apart).

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to the output CSV file to be created.
        merge_annotations (Optional[List[str]]): List of annotations for which tokens 
            should be merged. If None, all non-empty annotations will be considered 
            for merging.

    Returns:
        None

    Note:
        The input CSV should have the following columns:
        [encounter_id, note_id, token, start, end, annotation]
        Only tokens with annotations in the merge_annotations list will be combined.
    """
    with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        prev_row = None
        for row in reader:
            if prev_row is None:
                prev_row = row
                continue

            should_merge = (
                (merge_annotations is None and prev_row['annotation']) or
                (merge_annotations is not None and prev_row['annotation'] in merge_annotations)
            )

            if (should_merge and
                row['annotation'] == prev_row['annotation'] and 
                int(row['start']) - int(prev_row['end']) < 3):
                # Merge tokens
                prev_row['token'] += ' ' + row['token']
                prev_row['end'] = row['end']
            else:
                # Write the previous row and update prev_row
                writer.writerow(prev_row)
                prev_row = row

        # Write the last row
        if prev_row:
            writer.writerow(prev_row)