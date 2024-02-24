import requests

# Variables
OPENAI_API_KEY = "your_openai_api_key"
DATASET_PATH = "data/training_dataset.jsonl"
MODEL = "gpt-3.5-turbo"
# Optional: Add path to your validation dataset if we actually have one?
VALIDATION_DATASET_PATH = "path_to_your_validation_dataset.jsonl"

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

# Step 1: Upload the training dataset
print("Uploading training dataset...")
with open(DATASET_PATH, 'rb') as f:
    response = requests.post("https://api.openai.com/v1/files",
                             headers=headers,
                             files={"file": f},
                             data={"purpose": "fine-tune"})
    training_file_id = response.json()['id']
print(f"Training file uploaded: {training_file_id}")

# Optional: Upload the validation dataset (if we have one)
# Uncomment the following lines if you have a validation dataset
#print("Uploading validation dataset...")
#with open(VALIDATION_DATASET_PATH, 'rb') as f:
#    response = requests.post("https://api.openai.com/v1/files",
#                             headers=headers,
#                             files={"file": f},
#                             data={"purpose": "fine-tune"})
#    validation_file_id = response.json()['id']
#print(f"Validation file uploaded: {validation_file_id}")

# Step 2: Create the fine-tuning job
print("Creating fine-tuning job...")
data = {
    "model": MODEL,
    "training_file": training_file_id,
    # Optional: Add "validation_file": validation_file_id if you uploaded a validation dataset
}
response = requests.post("https://api.openai.com/v1/fine_tuning/jobs",
                         headers=headers,
                         json=data)
print(response.text)
