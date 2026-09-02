"""Entry point: a terminal chat REPL, or `python main.py --api` for the
FastAPI server.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.loop import run_agent  # noqa: E402
from agent.memory import ConversationMemory  # noqa: E402
from utils.config import get_settings  # noqa: E402
from utils.logging import get_logger  # noqa: E402

logger = get_logger("main")


def run_cli() -> None:
    settings = get_settings()
    memory = ConversationMemory(max_turns=settings.memory_max_turns)
    print("agent-starter-kit -- type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break
        reply = run_agent(memory, user_input)
        print(f"agent> {reply}\n")


def run_api() -> None:
    import uvicorn

    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    if "--api" in sys.argv:
        run_api()
    else:
        run_cli()
