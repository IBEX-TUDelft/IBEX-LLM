# Project Overview

This project is designed to streamline processes involving dataset preparation from log files, model fine-tuning using OpenAI's API, WebSocket connection management, and server process control. Its versatile components enable efficient handling of diverse tasks, from data manipulation to real-time communication and computational resource management.

## 📂 Project Structure

The repository is organized as follows, providing a clear and logical layout for easy navigation and understanding:

| File/Directory      | Description |
|---------------------|-------------|
| `README.md`         | An overview of the project, its purpose, instructions for use, and the integration of an LLM agent for specific actions. |
| `constructDataset.py` | Reads `.log.json` files from `jsonFiles`, extracts "log" data, and compiles it into a JSON Lines file in `data`. |
| `data/training_set.jsonl` | Generated dataset consisting of extracted log entries, ready for model training. |
| `finetune.py`       | Interacts with the OpenAI API to fine-tune a GPT model using the prepared dataset. |
| `handler.py`        | Manages WebSocket connections for real-time server-client communication and handles specific actions as instructed by LLM agents. |
| `jsonFiles`         | Contains source `.log.json` files used for dataset creation. |
| `killer.sh`         | Shell script to terminate server processes. |
| `serverStarter.sh`  | Initializes and starts server processes. |

## 🚀 Usage

### Preparing the Dataset

Generate your training dataset from log files:

```bash
python constructDataset.py
```

### Fine-tuning the Model

Initiate the model fine-tuning process with OpenAI:

```bash
python finetune.py
```

### Managing WebSocket Connections

Handle WebSocket communications and specific LLM agent instructions:

```bash
python handler.py
```

### Controlling the Server

Start and stop server processes as needed:

- **To start:** `sh serverStarter.sh`
- **To stop:** `sh killer.sh`

## ✅ Requirements

Ensure your environment meets the following prerequisites:

- **Python 3.x:** The primary programming language used.
- **OpenAI API Key:** Required for `finetune.py` to access OpenAI services.
- **WebSocket Support:** Necessary for the operation of `handler.py`.


## 📌 LLM Agent Integration

To facilitate the integration of an LLM agent for specific actions within this project, an initiating message format has been established. This format is designed to clearly communicate when and what action the LLM agent is required to perform:

```json
{
  "type": "event",
  "eventType": "action-required",
  "data": {
    "actionType": "SubmitCompensationRequest",
    "instructions": "You are now entering the Compensation Request Phase. Review the project proposals and submit your compensation request. Use the format: {'gameId':15,'type':'compensation-request','compensationRequests':[null,X]}, where X is your requested compensation amount as an integer.",
    "deadline": "You must submit your request before the timer ends at [timestamp].",
    "format": "{'gameId':15,'type':'compensation-request','compensationRequests':[null,X]}",
    "actionRequiredBy": "[timestamp]",
    "additionalInfo": "This phase is critical for negotiating compensation based on the project proposals. Your timely and accurate submission is essential."
  }
}
```

This message format is an example of what the LLM agent receives all necessary details to take action, including the action type, detailed instructions, deadlines, and the format for submissions. This integration is pivotal for automating and streamlining specific tasks within the project, particularly in phases requiring precise and timely submissions.

## 📚 Contributing

TODO
