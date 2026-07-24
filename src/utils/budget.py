import json
from pathlib import Path
from src.config import Settings

BUDGET_FILE = Path("budget_config.json")

def get_budget() -> float:
    """Read the budget threshold from local config. Defaults to 5.00."""
    if not BUDGET_FILE.exists():
        return 5.00
    try:
        data = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
        return float(data.get("budget", 5.00))
    except Exception:
        return 5.00


def set_budget(value: float) -> None:
    """Persist the budget threshold."""
    BUDGET_FILE.write_text(json.dumps({"budget": value}), encoding="utf-8")


def check_budget(current_cost: float) -> bool:
    """Return True if the current cost exceeds the budget."""
    return current_cost > get_budget()
