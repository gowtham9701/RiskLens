"""CSV import for holdings (manual ingestion path).

Expected columns: instrument_id, quantity, buy_price, buy_date (ISO).
Returns parsed rows and a list of validation errors; callers insert valid
rows as Holding records. Kept dependency-free (stdlib csv).
"""

from __future__ import annotations

import csv
import io
from typing import Any


REQUIRED = ["instrument_id", "quantity", "buy_price"]


def parse_holdings_csv(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    reader = csv.DictReader(io.StringIO(content))
    missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}"]
    for i, raw in enumerate(reader, start=2):
        try:
            rows.append({
                "instrument_id": raw["instrument_id"].strip(),
                "quantity": float(raw["quantity"]),
                "buy_price": float(raw["buy_price"]),
                "buy_date": (raw.get("buy_date") or "").strip() or None,
            })
        except (ValueError, KeyError) as e:
            errors.append(f"Row {i}: {e}")
    return rows, errors
