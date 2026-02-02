# Agentic AI

This repo is a workspace created to experience "agentic AI" concepts on local models. In this context, topics such as tool calling, reflection (self-evaluation), and autonomous code execution are examined.

All experiments are run locally via Ollama. It is possible to test these concepts in a completely local environment without depending on cloud APIs.


Model selection is a critical factor. A model capable of tool calling—that is, deciding when to call a function—is required. At the same time, it must be small enough to run on reasonable hardware.


## Content

### Tool Agent
There is a tool-using agent in the `ollama_agentic_tool.py` file. The model can call defined functions (such as querying time, writing files, generating QR codes) when necessary. Instead of the user giving direct commands, the model triggers the relevant function based on its own decision.

### Code Agent (Docker)
An agent that generates and executes code is located in the `code_agent_docker/` directory. This agent allows the model to execute the Python code it produces. For security purposes, all operations are isolated within a Docker container. Potentially harmful modules (`os`, `subprocess`, etc.) are blocked.

## Requirements

For the code to run:

1. **Ollama must be installed**
2. **The model must be loaded**

Ollama must be running in the background.

### Code Agent
```bash
cd agentic_ai/code_agent_docker
docker compose up --build

docker compose run code-agent


The Docker version uses network_mode: host, allowing access to Ollama at localhost:11434 from within the container.

Directory Structure
agentic_ai/
├── ollama_agentic_tool.py       # Tool-using agent
├── ollama_agentic_reflection.py # Reflection experiments (under construction)
├── code_agent_docker/           # Isolated code execution agent
│   ├── agent.py
│   ├── Dockerfile
│   └── docker-compose.yml
└── deeplearningai/              # Course notes and notebooks
Notes
The notebooks in the deeplearningai/ directory contain notes taken from DeepLearning.AI courses.