from __future__ import annotations

from dataclasses import dataclass

from .base import SimpleChapter


@dataclass(frozen=True)
class GovBondTradeBlueprint:
    """Deterministic Chapter 9 packaging of trade intent and controls."""

    trade_id: str
    instrument: str
    direction: str
    target_notional: float
    entry_level: float
    stop_level: float
    take_profit_level: float
    governance_status: str
    approved: bool
    scenario_value: float
    notes: tuple[str, ...] = ()


def compose_gov_bond_trade_blueprint(payload: dict[str, object]) -> GovBondTradeBlueprint:
    """Build a Chapter-9-ready blueprint from deterministic chapter exports."""
    required = {
        "trade_id",
        "instrument",
        "direction",
        "target_notional",
        "entry_level",
        "stop_level",
        "take_profit_level",
        "governance_status",
        "approved",
        "scenario_value",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Missing required blueprint fields: {missing}")

    return GovBondTradeBlueprint(
        trade_id=str(payload["trade_id"]),
        instrument=str(payload["instrument"]),
        direction=str(payload["direction"]),
        target_notional=float(payload["target_notional"]),
        entry_level=float(payload["entry_level"]),
        stop_level=float(payload["stop_level"]),
        take_profit_level=float(payload["take_profit_level"]),
        governance_status=str(payload["governance_status"]),
        approved=bool(payload["approved"]),
        scenario_value=float(payload["scenario_value"]),
        notes=tuple(str(note) for note in payload.get("notes", [])),
    )


class Chapter09(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="9", title="Chapter 9: Trade construction", objective="Convert valuation signals into position sizing and implementation checks.")
