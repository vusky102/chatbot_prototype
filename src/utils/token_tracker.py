import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import streamlit as st
import threading
from src.utils.model_pricing import get_cost

USAGE_LOG_FILE = Path("usage_log.json")
_log_lock = threading.Lock()


@dataclass
class UsageRecord:
    timestamp: str          # ISO format
    model: str
    provider: str
    operation: str          # "chat" | "embedding" | "caption" | "ingest"
    input_tokens: int
    output_tokens: int
    estimated_cost: float   # USD


class TokenTracker:
    def __init__(self):
        if "session_usage_records" not in st.session_state:
            st.session_state.session_usage_records = []

    def record(self, model: str, provider: str, operation: str, input_tokens: int, output_tokens: int) -> None:
        """Record usage in current session state and persist to log file."""
        cost = get_cost(model, input_tokens, output_tokens)
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            provider=provider,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost
        )
        
        # Add to session
        st.session_state.session_usage_records.append(record)
        
        # Persist to JSON
        self._append_to_log(record)

    def _append_to_log(self, record: UsageRecord) -> None:
        with _log_lock:
            try:
                logs = []
                if USAGE_LOG_FILE.exists():
                    try:
                        logs = json.loads(USAGE_LOG_FILE.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                logs.append(asdict(record))
                USAGE_LOG_FILE.write_text(json.dumps(logs, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"Failed to append to usage log: {e}")

    def get_session_totals(self) -> dict:
        """Get totals for the current session."""
        records = st.session_state.session_usage_records
        return {
            "total_input": sum(r.input_tokens for r in records),
            "total_output": sum(r.output_tokens for r in records),
            "total_cost": sum(r.estimated_cost for r in records),
            "num_calls": len(records)
        }

    def get_breakdown_by_model(self) -> list[dict]:
        """Aggregate session records by model."""
        records = st.session_state.session_usage_records
        models = {}
        for r in records:
            if r.model not in models:
                models[r.model] = {
                    "Model": r.model,
                    "Provider": r.provider,
                    "Input Tokens": 0,
                    "Output Tokens": 0,
                    "Cost ($)": 0.0,
                    "# Calls": 0
                }
            models[r.model]["Input Tokens"] += r.input_tokens
            models[r.model]["Output Tokens"] += r.output_tokens
            models[r.model]["Cost ($)"] += r.estimated_cost
            models[r.model]["# Calls"] += 1
        return list(models.values())

    def get_history_totals(self) -> dict:
        """Get total usage metrics across all historical records."""
        history = self.get_all_history()
        return {
            "total_input": sum(r.input_tokens for r in history),
            "total_output": sum(r.output_tokens for r in history),
            "total_cost": sum(r.estimated_cost for r in history),
            "num_calls": len(history)
        }

    def get_history_breakdown_by_model(self) -> list[dict]:
        """Aggregate all historical records by model."""
        history = self.get_all_history()
        models = {}
        for r in history:
            if r.model not in models:
                models[r.model] = {
                    "Model": r.model,
                    "Provider": r.provider,
                    "Input Tokens": 0,
                    "Output Tokens": 0,
                    "Cost ($)": 0.0,
                    "# Calls": 0
                }
            models[r.model]["Input Tokens"] += r.input_tokens
            models[r.model]["Output Tokens"] += r.output_tokens
            models[r.model]["Cost ($)"] += r.estimated_cost
            models[r.model]["# Calls"] += 1
        return list(models.values())

    def get_all_history(self) -> list[UsageRecord]:
        """Load all persistent history."""
        with _log_lock:
            if not USAGE_LOG_FILE.exists():
                return []
            try:
                data = json.loads(USAGE_LOG_FILE.read_text(encoding="utf-8"))
                return [UsageRecord(**r) for r in data]
            except Exception:
                return []

    def reset_session(self) -> None:
        """Clear session counters."""
        st.session_state.session_usage_records = []

    def clear_history(self) -> None:
        """Delete persistent log file."""
        with _log_lock:
            if USAGE_LOG_FILE.exists():
                USAGE_LOG_FILE.unlink()

    def export_csv(self) -> str:
        """Return all history as CSV string."""
        history = self.get_all_history()
        lines = ["Timestamp,Model,Provider,Operation,Input Tokens,Output Tokens,Estimated Cost ($)"]
        for r in history:
            lines.append(f"{r.timestamp},{r.model},{r.provider},{r.operation},{r.input_tokens},{r.output_tokens},{r.estimated_cost:.6f}")
        return "\n".join(lines)
