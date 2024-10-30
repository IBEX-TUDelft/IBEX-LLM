# Project Overview

This project introduces an approach to automating economic experiments by leveraging Large Language Models (LLMs). It uses OpenAI's API to create a multi-actor simulation environment where different LLM agents act as economic entities with distinct roles, preferences, and information. This setup aims to mimic complex economic scenarios within a digital platform, enabling efficient and ethical experimentation on a wide range of economic theories and institutional designs.

### Project Goals: Enhancing LLM Agent Reasoning in Economic Experiments
#### Note: These objectives evolve over time but are kept here for reference.

The project aims to improve the reasoning abilities of LLMs as agents in economic experiments, focusing on these key objectives:

#### 1. **Refine Instruction Parsing**
- **Goal:** Develop a more sophisticated parsing process that accurately interprets and summarizes complex instructions, ensuring LLM agents receive a rich, contextual understanding of their tasks.
- **Approach:** Enhance the summarization pipeline to preserve essential context and integrate clues that aid in understanding the broader economic scenarios.

#### 2. **Expand Context with Advanced Techniques**
- **Goal:** Utilize advanced machine learning techniques and dynamic prompting to enrich the context available to LLM agents, improving their decision-making in complex scenarios.
- **Approach:** Implement dynamic prompting strategies, integrate external knowledge bases, and explore ML models that specialize in context retention and understanding.

**Expected Outcome:** These improvements aim to make LLM agents’ reasoning more sophisticated and human-like, enhancing the fidelity of economic experiments and opening new avenues for economic research.

## 📂 Project Structure

| File/Directory                        | Description                                                                                                                                         |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `README.md`                           | Project documentation file.                                                                                                                         |
| `auction/`                            | Contains auction-related files, including test and handler files.                                                                                   |
| └── `AuctionTest.py`                  | Tests auction functionality.                                                                                                                        |
| └── `AuctionTestExtreme.py`           | Contains extreme test cases for auction functionality.                                                                                              |
| └── `GameHandlerAuction.py`           | Handles game logic for auction simulation.                                                                                                          |
| └── `LLMCommunicator.py`              | Manages communication between auction handlers and LLMs.                                                                                            |
| `config/`                             | Stores configuration files, database scripts, and architecture images.                                                                              |
| └── `architecture.svg`                | Diagram of the project architecture.                                                                                                                |
| └── `database.sql`                    | SQL database setup script.                                                                                                                          |
| `data/`                               | Contains all data-related files and subdirectories, including raw data, processed data, and output data.                                            |
| └── `output/`                         | Stores output files, such as logs and JSON results.                                                                                                 |
| └── `processed/`                      | Stores processed data for training models.                                                                                                          |
| └── `raw/`                            | Contains raw log files.                                                                                                                             |
| `examples.json`                       | Example game configurations for futarchy simulations.                                                                                               |
| `futurchy/`                           | Contains futarchy-related files, including test cases, game handlers, and scripts.                                                                  |
| └── `GameHandlerFutarchy.py`          | Handles futarchy game logic and interactions with LLM agents.                                                                                      |
| └── `WebSocketClient.py`              | Manages WebSocket communication for real-time interactions in futarchy games.                                                                       |
| `harberger/`                          | Contains harberger-related files, including game handlers and tests.                                                                                |
| `instructions/`                       | Contains instructional documents detailing how the project or certain components should be used.                                                    |
| `output/`                             | Stores general output files, mainly logs generated during simulations.                                                                              |
| `prompts/`                            | Stores predefined prompts used to communicate with LLM agents.                                                                                      |
| └── `button_prompt.txt`               | Button interaction prompt used in simulations.                                                                                                      |
| `scripts/`                            | Contains shell scripts to manage server processes and game simulations.                                                                             |
| └── `serverStarter.sh`                | Starts the server for simulations.                                                                                                                  |
| `src/`                                | Source directory housing all primary code, organized by functionality.                                                                              |
| └── `auction/`                        | Source code for auction-specific functionality.                                                                                                     |
| └── `futurchy/`                       | Source code for futarchy-specific functionality, including WebSocket and game handler.                                                              |
| └── `harberger/`                      | Source code for harberger-specific functionality.                                                                                                   |
| └── `voting/`                         | Source code for voting-based simulation games.                                                                                                      |
| `things_that_break/`                  | Experimental scripts and prototypes that are under development or testing.                                                                          |
| └── `GameHandlerAuction_Beta.py`      | Experimental version of auction game handler.                                                                                                       |
| `userentry.tex`                       | Document for user entry points in the LaTeX format.                                                                                                 |
| `voting/`                             | Contains voting game handler and related files.                                                                                                     |

## 🚀 Usage

### Preparing the Dataset

Extract and prepare the dataset from simulation logs for LLM training:

```bash
python constructDataset.py
```

### Fine-tuning the Model

Adapt LLM agents to specific economic behaviors and scenarios:

```bash
python finetune.py
```

### WebSocket Communication
Facilitate real-time decision-making and interaction in simulations:

```bash
python handler.py
```

### Controlling the Server

Start and stop server processes as needed:

- **To start:** `sh serverStarter.sh`
- **To stop:** `sh killer.sh`

## ✅ Requirements

Ensure your environment meets the following prerequisites:

- **Python 3.x:** The backbone of the project for scripting and data processing.
- **OpenAI API Key:** Essential for accessing LLM services and fine-tuning.
- **WebSocket Implementation:** Critical for real-time simulation and agent communication.

## Architecture Overview

![Alt text for the image](./config/architecture.svg)

## 📌 LLM Agent Integration Overview
Initially, the LLM agent is briefed using the same document provided to human subjects. The `instructionReader.py` script processes these documents by parsing, converting them to JSON format, and summarizing the content.

### Instruction Format

The instructions for the LLM agent are encapsulated in JSON format, including the project phases, such as requests, offers, and voting.

### Game Introduction Instructions

At the game's start, the LLM agent receives instructions defining how to respond to different events, ensuring a smooth integration and participation process.

### Action Required Message Example

An example message illustrates how the LLM agent receives detailed instructions for taking action, emphasizing the importance of precision and timeliness.

### Dynamic Scenario Simulation

Agents are dynamically assigned roles and objectives based on the specific economic theory or institutional design being tested. Each simulation can explore different facets of economic behavior, from market speculation to resource allocation, in a controlled yet complex virtual environment.