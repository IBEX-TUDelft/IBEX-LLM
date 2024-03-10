# Project Overview

This project is designed to streamline processes involving dataset preparation from log files, model fine-tuning using OpenAI's API, WebSocket connection management, and server process control. Its versatile components enable efficient handling of diverse tasks, from data manipulation to real-time communication and computational resource management.

## 📂 Project Structure

| File/Directory                          | Description                                                                                                                                      |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `README.md`                             | Provides an overview of the project, its purpose, instructions for use, and the integration of an LLM agent for specific actions.                |
| `src/constructDataset.py`               | Reads `.log.json` files from `data/raw`, extracts "log" data, and compiles it into a JSON Lines file in `data/processed`.                        |
| `data/`                                 | Contains all data-related files and subdirectories, including raw data, processed data, and output data.                                         |
| `data/raw/`                             | Houses source `.log.json` files used for dataset creation.                                                                                       |
| `data/processed/training_set_voting.jsonl` | Generated dataset consisting of extracted log entries, ready for model training. Stored within the `processed` subdirectory.                    |
| `data/output/`                          | Contains output files such as `outputAfter.txt` and `outputBefore.txt`, showcasing results or data transformations.                              |
| `src/finetune.py`                       | Interacts with the OpenAI API to fine-tune a GPT model using the prepared dataset located in `data/processed`.                                   |
| `src/handler.py`, `src/handlerNoGPT.py` | Manage WebSocket connections for real-time server-client communication and handle specific actions as instructed by LLM agents.                  |
| `config/token.txt`                      | Stores configuration details or sensitive information like API tokens.                                                                           |
| `instructions/`                         | Contains instructional documents in various formats (e.g., docx) that detail how the project or certain components should be used or operated.    |
| `src/instructionReader.py`              | Reads and formats instructions from documents in the `instructions/` directory and classifies how and when the instructions will be parsed.      |
| `scripts/killer.sh`, `scripts/serverStarter.sh` | Shell scripts for managing server processes, including initialization and termination.                                                         |

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

## Architecture Overview

![Alt text for the image](./config/architecture.svg)


## 📌 LLM Agent Integration Overview
Initially, the LLM agent is briefed using the same document provided to human subjects. The `instructionReader.py` script processes these documents by parsing, converting them to JSON format, and summarizing the content.

### Instruction Format

The instructions for the LLM agent are encapsulated in JSON format. Here is an example structure showcasing how the agent is briefed on the project's various phases, including an overview and key actions like requests, offers, and voting.

```json
{
    "Overview": [
        "The experiment simulates a democratic situation where owners vote. If the majority votes for the project, it gets developed. Players either implement a Project, or no Project is implemented."
    ],
    "Request": [
        "In the 'request' phase, the developer waits while owners make compensation requests. All requests are shown to the developer in the next phase, not to other voters."
    ],
    "Offer": [
        "After receiving requests, the developer sees the amounts in area 8. In area 10, they set the offer amount, the compensation offered to each owner if the Project is implemented. The developer's profit is visible if the offer is accepted."
    ],
    "Voting": [
        "In the voting phase, the developer is inactive, and owners vote on the project's development. Voting involves selecting an option in the tick boxes and pressing the vote button. If the majority votes in favor, the project is developed, and the developer pays the compensation amount to each owner. The game then progresses to the next round."
    ]
}
```

### Game Introduction Instructions

At the game's start, the LLM agent receives instructions defining how to respond to different events, ensuring a smooth integration and participation process.

```json
{
    "eventType": "introduction-instructions",
    "data": {
        "welcomeMessage": "Welcome to the Voting Game as an LLM agent.",
        "roleAssignment": "Your specific role and instructions will be provided at each game phase.",
        "responseTiming": "Prompt responses are crucial. Respond before the phase timer expires.",
        "responseFormat": "Responses should be in JSON format, with attributes as per instructions.",
        "example": {
            "actionType": "ExampleAction",
            "instructions": "Example response format: {\"gameId\":Y, \"type\":\"action-type\", \"details\":[\"specific details\"]}.",
            "actionRequiredBy": "Timely action is essential for game progression.",
            "additionalInfo": "Pay close attention to role-specific instructions for effective participation."
        }
    }
}
```

### Action Required Message Example

An example message illustrates how the LLM agent receives detailed instructions for taking action, emphasizing the importance of precision and timeliness.

```json
{
    "type": "event",
    "eventType": "action-required",
    "data": {
        "actionType": "SubmitCompensationRequest",
        "instructions": "Enter the Compensation Request Phase. Submit your request using the format: {'gameId':Y, 'type':'compensation-request', 'compensationRequests':[null,X]}, where X is your compensation amount.",
        "deadline": "Submit before the timer ends at [timestamp].",
        "format": "{'gameId':Y, 'type':'compensation-request', 'compensationRequests':[null,X]}",
        "actionRequiredBy": "[timestamp]",
        "additionalInfo": "This phase is crucial for project negotiation. Ensure your submission is timely and accurate."
    }
}
```
