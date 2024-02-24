# Project Overview

This project is designed to streamline processes involving dataset preparation from log files, model fine-tuning using OpenAI's API, WebSocket connection management, and server process control. Its versatile components enable efficient handling of diverse tasks, from data manipulation to real-time communication and computational resource management.

## 📂 Project Structure

The repository is organized as follows, providing a clear and logical layout for easy navigation and understanding:

| File/Directory      | Description |
|---------------------|-------------|
| `README.md`         | An overview of the project, its purpose, and instructions for use. |
| `constructDataset.py` | Reads `.log.json` files from `jsonFiles`, extracts "log" data, and compiles it into a JSON Lines file in `data`. |
| `data/training_set.jsonl` | Generated dataset consisting of extracted log entries, ready for model training. |
| `finetune.py`       | Interacts with the OpenAI API to fine-tune a GPT model using the prepared dataset. |
| `handler.py`        | Manages WebSocket connections for real-time server-client communication. |
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

Handle WebSocket communications:

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

## 📚 Contributing

TODO