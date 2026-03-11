# AI Price Agent (Deal Discovery + Pricing)

An autonomous, agent-based system that continuously:

- Scrapes fresh deals from RSS feeds.
- Uses LLMs (via LiteLLM) plus optional retrieval (Chroma) to estimate a fair price.
- Highlights high-discount opportunities in a Gradio dashboard with live logs and a vector plot.

**Entrypoint**: `price_agent/price_is_right.py`

---

## Quickstart (Windows / PowerShell)

From the `llm_engineering/` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set environment variables (PowerShell):

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
$env:LITELLM_LOG="1"
$env:LITELLM_LOG_PATH=".\litellm_calls.jsonl"
$env:GRADIO_SHARE="0"
```

Run the app:

```powershell
cd .\price_agent
..\.\.venv\Scripts\python.exe .\price_is_right.py
```

Then open the URL printed in the terminal (usually `http://127.0.0.1:7860`).

---

## Optional: build the vector database (RAG)

The Frontier/RAG agent can use a local Chroma DB. To build it:

```powershell
cd .\price_agent
..\.\.venv\Scripts\python.exe .\build_vectorstore.py --reset --n 800
```

This creates the folder `products_vectorstore/` (gitignored).

---

## Project structure

Top-level:

- `README.md`: how to run + architecture overview (this file)
- `requirements.txt`: pip dependencies
- `pyproject.toml` / `uv.lock`: project metadata + lockfile (if you use uv)
- `price_agent/`: the application package (UI + orchestration + agents)

Application code:

- `price_agent/price_is_right.py`: Gradio UI + timer loop + streaming logs + plot
- `price_agent/deal_agent_framework.py`: orchestration, Chroma connection, persisted memory
- `price_agent/log_utils.py`: log formatting for UI
- `price_agent/agents/`: all agents + data models
  - `agent.py`: base Agent class (logging + colors)
  - `planning_agent.py`: top-level orchestrator for each run
  - `scanner_agent.py`: RSS scrape + LLM selection/normalization of deals
  - `preprocessor.py`: optional LLM rewrite into a normalized product description
  - `ensemble_agent.py`: combines multiple price estimators
  - `frontier_agent.py`: RAG pricing (Chroma retrieval + LLM estimate)
  - `specialist_agent.py`: optional Modal-deployed fine-tuned model
  - `neural_network_agent.py` + `deep_neural_network.py`: optional local NN inference
  - `messaging_agent.py`: optional push alerts (disabled unless configured)
  - `deals.py`: RSS + HTML scraping + Pydantic schemas (`Deal`, `Opportunity`, etc.)
  - `llm_utils.py`: LiteLLM wrapper + optional JSONL request/response logging

Runtime artifacts (gitignored):

- `price_agent/memory.json`: persisted surfaced opportunities (used to avoid repeats)
- `price_agent/litellm_calls.jsonl`: JSONL call logs (when enabled)
- `products_vectorstore/`: Chroma persistent DB (if built)

---

## Application architecture (what runs where)

This is a single-process Python app with a UI loop:

- **UI layer**: Gradio Blocks in `price_is_right.py`
- **Orchestration layer**: `DealAgentFramework` in `deal_agent_framework.py`
- **Agent layer**: independent components in `agents/*`
- **External services** (optional): Gemini/OpenAI/etc via LiteLLM, Modal, Pushover
- **Local state**: `memory.json` + (optional) `products_vectorstore/`

### Runtime flow (high level)

1. Gradio loads and starts a periodic timer.
2. Each tick calls `DealAgentFramework.run()`.
3. The `PlanningAgent` coordinates:
   - `ScannerAgent`: fetch + pick best deals
   - `EnsembleAgent`: estimate fair price for each selected deal
   - `MessagingAgent`: optionally alert if discount exceeds threshold
4. The UI updates a table, live logs, and a vector plot (if available).

For diagrams and deeper notes, see `price_agent/ARCHITECTURE.md`.

---

## Agent architecture (responsibilities)

- **PlanningAgent**: “conductor” that decides what happens in one run.
- **ScannerAgent**: “finder” that scrapes RSS + asks an LLM to return a strict JSON list of candidate deals.
- **Preprocessor**: “normalizer” that rewrites raw descriptions into a consistent format.
- **EnsembleAgent**: “combiner” that blends estimates:
  - **FrontierAgent** (RAG): retrieve similar products from Chroma + ask an LLM for a price
  - **SpecialistAgent** (optional): call a remote fine-tuned model on Modal
  - **NeuralNetworkAgent** (optional): run local NN weights if present
- **MessagingAgent**: “notifier” that can send push alerts (only if `PUSHOVER_*` vars are set)

Each agent is designed to degrade gracefully (missing keys/DB/weights should not crash the app).

---

## Data architecture (schemas + persistence)

Core objects (defined in `price_agent/agents/deals.py`):

- **`ScrapedDeal`**: raw scraped RSS + HTML details/features (pre-LLM)
- **`Deal`**: model-selected deal with:
  - `product_description` (clean summary)
  - `price` (numeric)
  - `url`
- **`Opportunity`**: the final surfaced unit:
  - `deal: Deal`
  - `estimate: float`
  - `discount: float` (computed as `estimate - deal.price`)

Persistence:

- `memory.json` stores a list of `Opportunity` objects so the system can skip URLs already surfaced.
- `products_vectorstore/` (optional) stores embedded product examples used for retrieval-augmented pricing.

---

## Configuration

### Required (for Gemini via LiteLLM)

- `GEMINI_API_KEY`

### Optional

- **Logging**
  - `LITELLM_LOG=1` enables JSON logging of requests/responses
  - `LITELLM_LOG_PATH=.\litellm_calls.jsonl` writes JSONL (recommended)
- **Gradio**
  - `GRADIO_SHARE=1` enables a public Gradio share link
- **Push notifications (Pushover)**
  - `PUSHOVER_USER`, `PUSHOVER_TOKEN` enable push alerts
- **Modal specialist model**
  - `MODAL_ENABLED=1` enables `SpecialistAgent`
- **Preprocessor model route**
  - `PRICER_PREPROCESSOR_MODEL` (defaults to `ollama/llama3.2`)

---

## Observability / debugging

- **Live logs**: shown in the Gradio UI
- **LLM call logs** (optional JSONL):

```powershell
Get-Content .\litellm_calls.jsonl -Wait
```

---

## Safety / secrets

- Do **not** commit `.env` files or API keys.
- This repo ignores runtime artifacts like `litellm_calls.jsonl`, `memory.json`, and any Chroma DB folders.
