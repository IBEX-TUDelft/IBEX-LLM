import json
import os

class TrainingSetCreator:
    def __init__(self, input_directory, output_directory='data',
                 output_filename='training_set.jsonl'):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.output_filename = output_filename

    def collect_log_entries(self):
        log_entries = []

        # Iterate over each file in the input directory
        for filename in os.listdir(self.input_directory):
            if filename.endswith('.log.json'):
                file_path = os.path.join(self.input_directory, filename)

                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    if 'log' in data:
                        log_entries.append(data['log'])

        return log_entries

    def write_to_jsonl(self, log_entries):
        # Ensure the output directory exists
        os.makedirs(self.output_directory, exist_ok=True)

        output_path = os.path.join(self.output_directory, self.output_filename)

        with open(output_path, 'w', encoding='utf-8') as output_file:
            for entry in log_entries:
                output_file.write(json.dumps(entry) + '\n')

        print(
            f"Training set created with {len(log_entries)} entries in '{output_path}'.")

    def create_training_set(self):
        log_entries = self.collect_log_entries()
        self.write_to_jsonl(log_entries)


if __name__ == "__main__":
    directory_path = '/Users/jasperbruin/Documents/IBEX-LLM/jsonFiles'
    creator = TrainingSetCreator(input_directory=directory_path)
    creator.create_training_set()
