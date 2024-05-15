# TODO: Optimisation with https://arxiv.org/pdf/2308.16753.pdf, this suggests Context Aware Query Rewriting for Text Rankers using LLMs.
# Source: https://huggingface.co/docs/transformers/tasks/summarization

import json
from docx import Document
import os
from transformers import pipeline

class InstructionParser:
    """
    A class to parse, simplify, and summarize instructions from a document.

    Attributes:
        doc_path (str): The file path to the document containing instructions.
        instructions (dict): A dictionary to store instructions categorized by phases.
        summarizer (pipeline): A pipeline for summarizing text using a specified model.
    """

    def __init__(self, doc_path, model="sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the InstructionParser with a document path and a model for summarization.

        Parameters:
            doc_path (str): The file path to the document to parse.
            model (str, optional): The model identifier for the summarization pipeline. Defaults to "sshleifer/distilbart-cnn-12-6".
        """
        self.doc_path = doc_path
        self.instructions = {}
        self.summarizer = pipeline("summarization", model=model)

    def parse_instructions(self):
        """
        Parses instructions from the document, categorizing them by phase and
        specifically capturing the 'Overview of the experiment' section along with its subsequent text,
        until another section begins.
        """
        doc = Document(self.doc_path)
        current_phase = None
        capturing_overview = False  # Flag to indicate if we are currently capturing the overview section

        for para in doc.paragraphs:
            # Check for the start of the overview section
            if para.text.startswith("Overview of the experiment"):
                capturing_overview = True
                current_phase = "Overview"
                self.instructions[current_phase] = [para.text.strip()]
                continue  # Move to the next paragraph

            # If another phase starts, stop capturing the overview
            if para.text.startswith("Phase: "):
                capturing_overview = False  # Reset the flag as we move out of the overview
                current_phase = para.text.split("Phase: ")[1].strip()
                self.instructions[current_phase] = []
                continue

            # Continue capturing text for the overview or any other phase
            if capturing_overview or current_phase:
                if current_phase not in self.instructions:  # If for any reason current_phase is not set
                    self.instructions[current_phase] = []
                self.instructions[current_phase].append(para.text.strip())

        print(self.instructions)

    def simplify_instructions(self):
        """
        Simplifies instructions by keeping only the first two sentences of each instruction text.
        This method updates the `instructions` dictionary with simplified texts for each phase.
        """
        for phase, texts in self.instructions.items():
            simplified_texts = []
            for text in texts:
                if text:
                    segments = text.split('. ')
                    simplified_text = '. '.join(segments[:2])
                    simplified_texts.append(simplified_text)
            self.instructions[phase] = simplified_texts

    def summarize_instructions(self):
        """
        Summarizes the instructions for each phase using the summarization pipeline.
        This method updates the `instructions` dictionary with a summary text for each phase.
        """
        for phase, texts in self.instructions.items():
            full_text = " ".join(texts)
            summary = self.summarizer(full_text, max_length=130, min_length=30, do_sample=False)
            self.instructions[phase] = [summary[0]['summary_text']]

    def save_instructions_to_json(self, json_path):
        """
        Saves the processed instructions to a JSON file at the specified path.
        Creates the directory if it does not exist.

        Parameters:
            json_path (str): The file path where the JSON file will be saved.
        """
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as json_file:
            json.dump(self.instructions, json_file, indent=4)

# Example usage
doc_path = '../instructions/VotingInstructions_V2.docx'
json_path = '../data/processed/instructions.json'

parser = InstructionParser(doc_path)
parser.parse_instructions()  # Parse instructions from the document
parser.simplify_instructions()  # Simplify the parsed instructions
parser.summarize_instructions()  # Summarize the simplified instructions
parser.save_instructions_to_json(json_path)  # Save the summarized instructions to a JSON file

print(f"Instructions have been parsed, simplified, and summarized before saving to {json_path}")
