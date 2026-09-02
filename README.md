# agent-starter-kit

[![CI](https://github.com/asadullah48/agent-starter-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/asadullah48/agent-starter-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A minimal, **working** AI agent built on the Claude API -- organized so it
stays maintainable once you add more tools, memory, APIs, tests, or
teammates, instead of living in one growing Python file. Runs against
Claude out of the box, or completely free and local via Ollama.

## Live demo

**https://agent-starter-kit-six.vercel.app**

- [`/health`](https://agent-starter-kit-six.vercel.app/health) -- liveness check
- [`/docs`](https://agent-starter-kit-six.vercel.app/docs) -- interactive OpenAPI docs (try `/chat` from here)
- `POST /chat` runs in a safe "demo mode" (explains itself instead of
  erroring) because no `ANTHROPIC_API_KEY` is set on the deployment -- a
  public endpoint with a real key attached would let any visitor spend
  it. Clone the repo and add your own key (or `LLM_PROVIDER=ollama`) to
  try the full agent. Note the deployment is also stateless per-request,
  so multi-turn memory only works locally, not against the hosted demo.

## What's here

One folder = one responsibility:

```
agent-starter-kit/
??? README.md               Documentation & setup (this file)
??? LICENSE                 MIT
??? requirements.txt         Runtime dependencies
??? requirements-dev.txt      + pytest, for running the test suite
??? .env.example               API keys & environment variables (copy to .env)
??? .gitignore
??? docker-compose.yml         Runs the API in a container
??? Dockerfile
??? vercel.json                 Serverless function config for the live demo
??? main.py                     CLI entry point (chat REPL or --api server)
??? pytest.ini
??? api/index.py                 Vercel entrypoint (re-exports src/api/app.py)
??? .github/workflows/ci.yml     Runs the test suite on every push/PR
??? src/
?   ??? agent/                Agent loop, state, and memory
?   ?   ??? loop.py             The tool-calling execution loop
?   ?   ??? memory.py           Turn-based, size-bounded conversation history
?   ?   ??? state.py            Per-session state
?   ??? tools/                Calculator, currency conversion, knowledge-base search
?   ?   ??? calculator.py
?   ?   ??? currency.py         Real external API (apilayer.com), free tier
?   ?   ??? knowledge_base.py
?   ??? models/                LLM provider configuration
?   ?   ??? llm.py               Anthropic (Claude) or Ollama (free, local) -- one switch
?   ??? prompts/                System prompts and reusable templates
?   ?   ??? system_prompt.md
?   ?   ??? system.py
?   ?   ??? templates.py
?   ??? utils/                  Logging, configuration & helpers
?   ?   ??? config.py
?   ?   ??? logging.py
?   ??? api/                    FastAPI routes and schemas
?       ??? app.py
?       ??? schemas.py
??? tests/                    Agent, tool, and API tests
??? data/                     Sample datasets / knowledge base
??? logs/                     Runtime logs (app.log)
```

## Why this layout?

- Need a new capability? Add it to `tools/`.
- Changing the LLM or its settings? Update `models/` or `utils/config.py`.
- Improving the agent's behavior? Look in `agent/` or `prompts/`.
- Something breaks? Tests and `logs/app.log` tell you where to start.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # then edit .env

python main.py               # chat in the terminal
python main.py --api         # or serve the API on :8000
```

### Run it for free with Ollama (no API key)

```bash
ollama pull llama3.1
ollama serve
```

```
# in .env
LLM_PROVIDER=ollama
```

### With Docker

```bash
docker compose up --build
```

### Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

19 tests, all mocked -- no network calls, no API key required to run the
suite. CI runs the same command on every push and PR.

## Design notes

- **Model**: defaults to `claude-opus-5` via `CLAUDE_MODEL`; switch the
  whole app to a free local model with `LLM_PROVIDER=ollama` -- see
  `src/models/llm.py`, the only file that talks to either provider. The
  Ollama path translates our Anthropic-shaped message/tool format to and
  from Ollama's chat API so `agent/loop.py` never has to know which
  provider is active.
- **Memory**: `agent/memory.py` groups history into whole "turns" and
  trims the oldest ones once `AGENT_MEMORY_MAX_TURNS` is exceeded, so a
  `tool_use`/`tool_result` pair is never split across the trim boundary
  (which the Messages API would reject). See the module docstring for the
  truncate-vs-summarize trade-off and the upgrade path to summarization.
- **Tools**: every tool lives in its own module under `src/tools/` and
  exports a `TOOL_DEF` schema + a same-named function; `src/tools/__init__.py`
  is the only place that needs to know a new tool exists. `currency.py`
  is a real external API integration (apilayer.com, free tier) --
  the template for wiring in any other apilayer product.
- **Errors**: a failing tool call -- bad input, a missing API key, a
  network error -- becomes an `is_error` tool_result, not a crash. Claude
  sees the failure and can retry, ask for clarification, or explain it.
- **Serverless-safe**: `utils/logging.py` falls back to console-only
  logging on a read-only filesystem instead of crashing on import, so the
  same code runs locally and on Vercel.

## Adding a tool

1. Create `src/tools/my_tool.py` exporting `TOOL_DEF` (the JSON schema
   Claude sees) and a function of the same name as `TOOL_DEF["name"]`.
2. Register both in `src/tools/__init__.py`'s `_REGISTRY` and
   `_DEFINITIONS`.

That's it -- `agent/loop.py` and the API never need to change.

## Redeploying / updating the demo

The project is linked to Vercel via `vercel link` and connected to this
GitHub repo, so a push to `main` triggers a new deployment automatically.
To deploy manually:

```bash
vercel deploy --prod
```

To take `/chat` out of demo mode, set `ANTHROPIC_API_KEY` as a project
environment variable in the Vercel dashboard (Settings -> Environment
Variables) and redeploy.
