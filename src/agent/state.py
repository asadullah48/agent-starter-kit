"""Per-session agent state."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentState:
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_count: int = 0

    def record_turn(self) -> None:
        self.turn_count += 1
