# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WizLedger is a credit card/bank statement processor that uses LangGraph workflows to extract transactions from PDF statements using OCR and AI-based correction. The application provides both a Gradio UI and a REST API for processing financial statements.

## Development Commands

### Running the Application

```bash
# Windows
run.bat

# Linux/MacOS
./run.sh
```

The application starts on `http://localhost:7860` with both Gradio UI and FastAPI endpoints.

### Docker Commands

```bash
# Build local image
docker build -t wizledger .

# Run container
docker run -d -p 7860:7860 \
    -e OPENROUTER_MODEL="anthropic/claude-4.5-sonnet" \
    -e OPENROUTER_API_URL="https://openrouter.ai/api/v1" \
    -e OPENROUTER_API_KEY="<your-key>" \
    wizledger
```

### Environment Setup

Copy `.env.example` to `.env` and configure:
- `OPENROUTER_API_KEY`: Required for LLM-based transaction extraction
- `OPENROUTER_MODEL`: Model to use (default: anthropic/claude-4.5-sonnet)
- `OPENROUTER_API_URL`: API endpoint (default: https://openrouter.ai/api/v1/chat/completions)

## Architecture

### LangGraph Workflow

The application uses a LangGraph state machine with memory checkpointing to process statements through the following nodes:

```
ocr → extract → display_transactions → get_human_input → process_human_input → check_if_done
                       ↑                                                            ↓
                       └────────────────────────(continue)─────────────────────────┘
                                                                                    ↓
                                                                                (done)
                                                                                    ↓
                                                                              store_csv
```

**Key workflow characteristics:**
- Uses `MemorySaver` checkpointer for state persistence across human interactions
- Interrupts before `get_human_input` to allow user corrections
- Supports thread-based sessions with unique `thread_id` for concurrent processing
- State is defined in `src/utils/state.py` as a TypedDict

### Core Components

**src/main.py**: Defines the LangGraph workflow
- Assembles all nodes into the state graph
- Configures conditional edges and interrupt points
- Provides `process_stream()` for CLI and `process_file_from_ui()` for web interface
- Creates compiled app with memory: `app = workflow.compile(checkpointer=memory, interrupt_before=["get_human_input"])`

**src/ui.py**: Gradio + FastAPI application
- Mounts Gradio interface on FastAPI for hybrid UI/API deployment
- Main endpoints:
  - POST `/process`: Upload statement and start processing
  - POST `/continue_processing`: Resume workflow with human corrections
  - POST `/export_transactions`: Export transactions to CSV
- Uses temporary files for uploads and exports
- CORS enabled for cross-origin requests

**src/nodes/**: Individual workflow nodes
- `ocr_node.py`: Performs OCR on PDF using MarkItDown
- `extract_node.py`: Uses LLM to extract structured transactions from OCR text
- `display_transactions_node.py`: Formats transactions for display
- `get_human_input_node.py`: Interrupt point for human review
- `process_human_input_node.py`: Processes user corrections/confirmations
- `check_if_done_node.py`: Determines if workflow continues or completes
- `store_csv_node.py`: Exports final transactions to CSV

### Data Models

**src/models/transactions.py**:
- `Transaction`: Pydantic model with fields: date (YYYY-MM-DD), description, amount (float, negative for debits)
- `Transactions`: RootModel wrapping List[Transaction] for LLM structured output

**src/utils/state.py**:
- `State`: TypedDict containing workflow state
- Fields: file_path, ocr_text, transactions, human_input, is_done, error

### Utilities

**src/utils/ocr_utils.py**:
- `perform_ocr_pdf()`: Performs OCR using MarkItDown library
- MarkItDown is used for simplicity and no API quota limits

**src/utils/transaction_utils.py**:
- `extract_transactions()`: Uses LangChain + OpenRouter API to extract structured transactions
- Chain: `prompt | llm | PydanticOutputParser`
- Note: OpenRouter doesn't support `.with_structured_output()`, so uses parser instead
- `store_transactions_csv()`: Saves transactions to CSV file

**src/utils/decorators.py**:
- Contains `@log_node_entry_exit` decorator for node execution logging

**src/utils/human_input_utils.py**:
- Contains utilities for processing human input during workflow interruptions

## Important Implementation Details

### OCR Processing
- Uses MarkItDown library (no API key required)
- PDF files only - raises ValueError for non-PDF formats

### LLM Integration
- Uses LangChain's ChatOpenAI with OpenRouter API
- OpenRouter doesn't support structured output natively, requires PydanticOutputParser
- Model and credentials configured via environment variables at runtime

### State Management
- LangGraph uses MemorySaver for checkpointing
- Thread IDs are UUIDs generated per session
- State updates use `app.update_state(thread, data, as_node="node_name")`
- Workflow can be resumed with `app.stream(None, thread, ...)`

### API Thread Safety
- Each request gets a unique thread_id
- Thread ID must be passed to `/continue_processing` to maintain session context
- Temporary files are cleaned up after processing

### Output Structure
- Transactions are list of dicts with keys: date, description, amount
- CSV export uses pandas DataFrame conversion
- Output folder stores exported CSV files

## Testing Locally

1. Place sample PDF statements in the `input/` folder
2. Run the application using `run.bat` or `./run.sh`
3. Access Gradio UI at http://localhost:7860
4. Upload statement, review extracted transactions, provide corrections if needed
5. Export to CSV when satisfied

For API testing, see examples in README.md or the "API Usage" tab in Gradio UI.
