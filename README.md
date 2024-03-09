# Project Overview

This project is designed to streamline processes involving dataset preparation from log files, model fine-tuning using OpenAI's API, WebSocket connection management, and server process control. Its versatile components enable efficient handling of diverse tasks, from data manipulation to real-time communication and computational resource management.

## 📂 Project Structure

The repository is organized as follows, providing a clear and logical layout for easy navigation and understanding:

| File/Directory            | Description                                                                                                                                       |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `README.md`               | An overview of the project, its purpose, instructions for use, and the integration of an LLM agent for specific actions.                          |
| `constructDataset.py`     | Reads `.log.json` files from `jsonFiles`, extracts "log" data, and compiles it into a JSON Lines file in `data`.                                  |
| `data/training_set.jsonl` | Generated dataset consisting of extracted log entries, ready for model training.                                                                  |
| `finetune.py`             | Interacts with the OpenAI API to fine-tune a GPT model using the prepared dataset.                                                                |
| `handler.py`              | Manages WebSocket connections for real-time server-client communication and handles specific actions as instructed by LLM agents.                 |
| `jsonFiles`               | Contains source `.log.json` files used for dataset creation.                                                                                      |
| `killer.sh`               | Shell script to terminate server processes.                                                                                                       |
| `instructionReader.py`    | Reads and formats instructions from a given pdf or doc file and that will classify how and when the instructions will be parsed to the LLM agent. |
| `serverStarter.sh`        | Initializes and starts server processes.                                                                                                          |

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


To refine the "LLM Agent Integration" section for clarity and effectiveness, we can focus on making the instructions more direct and structured, ensuring all critical information is easily accessible and understandable. Here's a fine-tuned version:

## 📌 LLM Agent Integration Overview
Initially, the LLM agent is briefed using the same document provided to human subjects. The `instructionReader.py` script processes these documents by parsing, converting them to JSON format, and summarizing the content. This ensures that the LLM agent receives brief and concise prompts, facilitating efficient and accurate task execution.

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

This refined structure provides a clear, detailed guide for integrating LLM agents into the project, specifying the instruction format, initial briefing, and example action messages. This approach ensures the agent is well-prepared to perform required tasks efficiently and effectively.

## 📚 Contributing

TODO
