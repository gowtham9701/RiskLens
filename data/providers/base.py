"""Data-provider adapter interface.

Financial calculations never depend on a concrete provider. Each real
provider (RBI, CCIL, NSE, BSE, CRISIL, ICRA, AMFI, news APIs, ...) should
implement this interface and write into the canonical database tables.
The shipped build uses the SimulatedProvider only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ProviderResult:
    source: str
    retrieved_at: datetime
    feed_status: str  # "real-time" | "delayed" | "end-of-day" | "simulated"
    records: list[dict[str, Any]]


class DataProvider(ABC):
    """Base adapter. Subclass per provider; keep credentials in env vars."""

    name: str = "abstract"
    feed_status: str = "simulated"

    @abstractmethod
    def fetch_prices(self, instrument_ids: list[str]) -> ProviderResult: ...

    @abstractmethod
    def fetch_ratings(self, issuer_ids: list[str]) -> ProviderResult: ...

    @abstractmethod
    def fetch_news(self, issuer_ids: list[str]) -> ProviderResult: ...


class SimulatedProvider(DataProvider):
    """Reads from the bundled simulated dataset — the default dev mode."""

    name = "SIM-FEED"
    feed_status = "simulated"

    def __init__(self, dataset: dict[str, Any]):
        self._data = dataset

    def _result(self, records: list[dict]) -> ProviderResult:
        return ProviderResult(self.name, datetime.utcnow(), "simulated", records)

    def fetch_prices(self, instrument_ids: list[str]) -> ProviderResult:
        ids = set(instrument_ids)
        return self._result([p for p in self._data.get("market_prices", [])
                             if p["instrument_id"] in ids])

    def fetch_ratings(self, issuer_ids: list[str]) -> ProviderResult:
        ids = set(issuer_ids)
        return self._result([r for r in self._data.get("credit_ratings", [])
                             if r["issuer_id"] in ids])

    def fetch_news(self, issuer_ids: list[str]) -> ProviderResult:
        ids = set(issuer_ids)
        return self._result([n for n in self._data.get("news", [])
                             if n.get("issuer_id") in ids])
