# AutoDeal (generic name)

An autonomous, agent-based system that:

- Scrapes fresh deals from RSS feeds.
- Uses LLMs (Gemini via LiteLLM) + retrieval (Chroma) to estimate a fair price.
- Surfaces discounted opportunities in a Gradio dashboard with live logs.

The entrypoint is a Gradio app: `price_agent/price_is_right.py`.

## What this project does

At a high level, the system runs an automated loop:

1. Fetch new deals from RSS.
2. Use an LLM to select the most promising deals and normalize their descriptions.
3. Estimate a fair price using an ensemble of agents (RAG + optional specialist + optional neural net).
4. Display results in a UI with full request/response logging.

## Architecture (runtime data flow)

- **UI**: `price_agent/price_is_right.py`
- **Orchestrator**: `price_agent/deal_agent_framework.py`
- **Agents**: `price_agent/agents/*`

Core flow:

- `Gradio Timer/UI` -> `DealAgentFramework.run()`
- `PlanningAgent` orchestrates:
  - `ScannerAgent` (RSS scrape + LLM deal selection)
  - `Preprocessor` (optional LLM cleanup/normalization)
  - `EnsembleAgent` combines:
    - `FrontierAgent` (RAG: Chroma retrieval + LLM estimate)
    - `SpecialistAgent` (optional: remote fine-tuned model via Modal)
    - `NeuralNetworkAgent` (optional: local NN weights)

More detailed notes and diagrams are in `price_agent/ARCHITECTURE.md`.

## Setup

### 1) Create a virtual environment

From the `llm_engineering/` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) Configure environment variables

From `llm_engineering/price_agent`:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
$env:LITELLM_LOG="1"
$env:LITELLM_LOG_PATH=".\litellm_calls.jsonl"
$env:GRADIO_SHARE="0"
```

Notes:

- `GEMINI_API_KEY` is required to use Gemini.
- `LITELLM_LOG_PATH` writes JSONL logs of every LLM call.
- `GRADIO_SHARE=1` creates a public share link.

### 3) (Optional) Build the vector database for RAG

This creates a local Chroma DB used by the RAG agent:

```powershell
..\.\.venv\Scripts\python.exe .\build_vectorstore.py --reset --n 800
```

### 4) Run the app

```powershell
..\.\.venv\Scripts\python.exe .\price_is_right.py
```

Open the URL printed in the terminal (usually `http://127.0.0.1:7860`).

## Debugging and observability

- **Live logs**: shown inside the Gradio UI
- **LLM call logs**:
  - Terminal output
  - JSONL file at `LITELLM_LOG_PATH` (if set)

To tail the JSONL file:

```powershell
Get-Content .\litellm_calls.jsonl -Wait
```

## Safety / secrets

- Do not commit `.env` or API keys.
- This repo ignores runtime artifacts like `litellm_calls.jsonl`, `memory.json`, and any Chroma DB folders.
