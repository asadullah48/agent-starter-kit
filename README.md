# agent-starter-kit

A minimal, **working** Claude-powered AI agent, organized so it stays
maintainable once you add more tools, memory, APIs, tests, or teammates --
instead of living in one growing Python file.

One folder = one responsibility:

```
agent-starter-kit/
├── README.md            Documentation & setup (this file)
├── requirements.txt      Dependencies
├── .env.example           API keys & environment variables (copy to .env)
├── .gitignore
├── docker-compose.yml     Runs the API in a container
├── main.py                CLI entry point (chat REPL or --api server)
├── pytest.ini
├── src/
│   ├── agent/              Agent loop, state, and memory
│   │   ├── loop.py           The tool-calling execution loop
│   │   ├── memory.py         Turn-based, size-bounded conversation history
│   │   └── state.py          Per-session state
│   ├── tools/               Calculator, knowledge-base search, custom tools
│   │   ├── calculator.py
│   │   └── knowledge_base.py
│   ├── models/              LLM client configuration
│   │   └── llm.py            The only file that talks to the Anthropic SDK
│   ├── prompts/              System prompts and reusable templates
│   │   ├── system_prompt.md
│   │   ├── system.py
│   │   └── templates.py
│   ├── utils/                Logging, configuration & helpers
│   │   ├── config.py
│   │   └── logging.py
│   └── api/                  FastAPI routes and schemas
│       ├── app.py
│       └── schemas.py
├── tests/                  Agent, tool, and API tests
├── data/                   Sample datasets / knowledge base
└── logs/                   Runtime logs (app.log)
```

## Why this layout?

- Need a new capability? Add it to `tools/`.
- Changing the LLM or its settings? Update `models/` or `utils/config.py`.
- Improving the agent's behavior? Look in `agent/` or `prompts/`.
- Something breaks? Tests and `logs/app.log` tell you where to start.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY

# 3. Chat in the terminal
python main.py

# ...or run the API
python main.py --api
# POST http://localhost:8000/chat  {"message": "hi", "session_id": "me"}
```

### With Docker

```bash
docker compose up --build
```

### Running tests

```bash
pytest
```

Tests never call the real Anthropic API -- `tests/test_api.py` mocks
`run_agent`, and the tool/memory tests exercise pure logic. No API key is
required to run the test suite.

## Design notes

- **Model**: defaults to `claude-opus-5` via `CLAUDE_MODEL` in `.env` --
  change it per-environment without touching code.
- **Memory**: `agent/memory.py` groups history into whole "turns" and
  trims the oldest ones once `AGENT_MEMORY_MAX_TURNS` is exceeded, so a
  `tool_use`/`tool_result` pair is never split across the trim boundary
  (which the Messages API would reject). See the module docstring for the
  truncate-vs-summarize trade-off and the upgrade path to summarization.
- **Tools**: every tool lives in its own module under `src/tools/` and
  exports a `TOOL_DEF` schema + a same-named function; `src/tools/__init__.py`
  is the only place that needs to know a new tool exists.
- **Errors**: a failing tool call becomes an `is_error` tool_result, not a
  crash -- Claude sees the failure and can retry, ask for clarification,
  or explain it to the user.

## Adding a tool

1. Create `src/tools/my_tool.py` exporting `TOOL_DEF` (the JSON schema
   Claude sees) and a function of the same name as `TOOL_DEF["name"]`.
2. Register both in `src/tools/__init__.py`'s `_REGISTRY` and
   `_DEFINITIONS`.

That's it -- `agent/loop.py` and the API never need to change.
