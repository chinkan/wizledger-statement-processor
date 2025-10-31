---
title: WizLedger - Monthly Statement Processor
emoji: 💳
colorFrom: indigo
colorTo: yellow
sdk: gradio
sdk_version: 4.43.0
app_file: src/ui.py
pinned: false
license: mit
---

# WizLedger - Monthly Statement Processor

## Introduction

This project demonstrates a credit card statement assistant that can process PDF statements, perform OCR, and use LangGraph for AI-based transaction corrections.

### Demo

https://github.com/user-attachments/assets/a7f5a839-c7bd-4598-bdfe-9c2168008657

### Try it on HuggingFace

https://huggingface.co/spaces/chinkanai/wizledger

## Technologies

-   LangChain
-   LangGraph
-   MarkItDown
-   OpenRouter API (for access Claude 4.5 Sonnet) [OpenRouter API](https://openrouter.ai/)
-   pdf2image (optional) [pdf2image](https://pdf2image.readthedocs.io/en/latest/)

## LangGraph

Here is the graph of the workflow:

```mermaid
graph TD
    Start((Start)) --> A[ocr]
    A --> B[extract]
    B --> C[display_transactions]
    C --> D[get_human_input]
    D --> E[process_human_input]
    E --> F{check_if_done}
    F -->|continue| C
    F -->|done| G[store_csv]
    G --> End((End))

    style Start fill:#4CAF50,stroke:#333,stroke-width:2px
    style End fill:#FF5722,stroke:#333,stroke-width:2px
```

## Prerequisites

-   Python 3.10 or later
-   OpenRouter API key (Get it [here](https://openrouter.ai/))

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/chinkan/demo-ai-statement-extract
    cd demo-ai-statement-extract
    ```

2. Configure environment variables:

    - Copy `.env.example` to `.env`
    - Fill in the variables in the `.env` file

3. Run it

    - On Windows

    ```bash
    run.bat
    ```

    - On Linux or MacOS

    ```bash
    ./run.sh
    ```

## Output

Processed data will be saved in the `output` folder.

## Docker run from build local

### Build the image

```bash
docker build -t wizledger .
```

### Run the container

**Linux/MacOS:**

```bash
docker run -d -p 7860:7860 \
    -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" \
    -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" \
    -e OPENROUTER_API_KEY="<replace with your openrouter api key>" \
    wizledger
```

**Windows (PowerShell):**

```powershell
docker run -d -p 7860:7860 `
    -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" `
    -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" `
    -e OPENROUTER_API_KEY="<replace with your openrouter api key>" `
    wizledger
```

**Windows (Command Prompt):**

```cmd
docker run -d -p 7860:7860 -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" -e OPENROUTER_API_KEY="<replace with your openrouter api key>" wizledger
```

## Docker run from huggingface

**Linux/MacOS:**

```bash
docker run -it -p 7860:7860 --platform=linux/amd64 \
	-e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" \
	-e OPENROUTER_API_URL="https://openrouter.ai/api/v1" \
	-e OPENROUTER_API_KEY="<replace with your openrouter api key>" \
	registry.hf.space/chinkanai-wizledger:latest python src/ui.py
```

**Windows (PowerShell):**

```powershell
docker run -it -p 7860:7860 --platform=linux/amd64 `
	-e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" `
	-e OPENROUTER_API_URL="https://openrouter.ai/api/v1" `
	-e OPENROUTER_API_KEY="<replace with your openrouter api key>" `
	registry.hf.space/chinkanai-wizledger:latest python src/ui.py
```

**Windows (Command Prompt):**

```cmd
docker run -it -p 7860:7860 --platform=linux/amd64 -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" -e OPENROUTER_API_KEY="<replace with your openrouter api key>" registry.hf.space/chinkanai-wizledger:latest python src/ui.py
```

## Docker run from GitHub Container Registry

**Linux/MacOS:**

```bash
docker run -d -p 7860:7860 \
	-e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" \
	-e OPENROUTER_API_URL="https://openrouter.ai/api/v1" \
	-e OPENROUTER_API_KEY="<replace with your openrouter api key>" \
	ghcr.io/chinkan/wizledger-statement-processor:master
```

**Windows (PowerShell):**

```powershell
docker run -d -p 7860:7860 `
	-e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" `
	-e OPENROUTER_API_URL="https://openrouter.ai/api/v1" `
	-e OPENROUTER_API_KEY="<replace with your openrouter api key>" `
	ghcr.io/chinkan/wizledger-statement-processor:master
```

**Windows (Command Prompt):**

```cmd
docker run -d -p 7860:7860 -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" -e OPENROUTER_API_KEY="<replace with your openrouter api key>" ghcr.io/chinkan/wizledger-statement-processor:master
```

## API

```python
import requests
import json
# Process a new statement
url = "http://localhost:7860/process"
files = {
    'statement': ('statement.pdf', open('path/to/statement.pdf', 'rb'), 'application/pdf'),
}
response = requests.post(url, files=files)
result = response.json()
print(result['result'])
thread_id = result['thread_id']

# Continue processing
url = "http://localhost:7860/continue_processing"
data = {
    'human_input': 'Some human input',
    'thread_id': thread_id
}
response = requests.post(url, json=data)
print(response.json())
result = response.json()

# Export transactions
url = "http://localhost:7860/export_transactions"
data = {'output': json.dumps(result)}
response = requests.post(url, json=data)

# Display the transactions
import pandas as pd
import io
df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8')
display(df)
```

## Contributing

We welcome contributions! To contribute to the project:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push to your branch and create a pull request.

## License

This project is licensed under the MIT License.
