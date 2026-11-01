"""Credit rating normalisation across Indian agencies.

Maps agency-specific long-term rating symbols to an ordinal rank
(1 = highest quality) and a coarse grade bucket. Ratings are NOT
converted into guaranteed default probabilities.
"""

from __future__ import annotations

from typing import Optional

# Normalised long-term scale (CRISIL/ICRA/CARE/India Ratings share
# broadly equivalent symbols). Rank 1 = AAA / Sovereign.
_RATING_RANK = {
    "SOV": 1, "SOVEREIGN": 1,
    "AAA": 1,
    "AA+": 2, "AA": 2, "AA-": 3,
    "A+": 3, "A": 4, "A-": 4,
    "BBB+": 5, "BBB": 5, "BBB-": 6,
    "BB+": 7, "BB": 7, "BB-": 8,
    "B+": 8, "B": 9, "B-": 9,
    "C": 10,
    "D": 11,
}

_INVESTMENT_GRADE_MAX_RANK = 6  # BBB- and better


def normalise_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    # strip agency prefixes like "CRISIL AAA", "[ICRA]AA+", "IND AA"
    for token in ("CRISIL", "ICRA", "CARE", "IND", "[", "]"):
        s = s.replace(token, "")
    return s.strip()


def rating_rank(symbol: Optional[str]) -> Optional[int]:
    """Return ordinal rank (1 best). None if unknown/missing."""
    if not symbol:
        return None
    return _RATING_RANK.get(normalise_symbol(symbol))


def is_investment_grade(symbol: Optional[str]) -> Optional[bool]:
    rank = rating_rank(symbol)
    if rank is None:
        return None
    return rank <= _INVESTMENT_GRADE_MAX_RANK


def grade_bucket(symbol: Optional[str]) -> str:
    rank = rating_rank(symbol)
    if rank is None:
        return "Unrated"
    if rank == 1:
        return "AAA/Sovereign"
    if rank <= 3:
        return "AA"
    if rank <= 4:
        return "A"
    if rank <= 6:
        return "BBB"
    if rank <= 9:
        return "Speculative"
    return "Distressed/Default"
