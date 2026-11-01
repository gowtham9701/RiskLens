"""Generate the RiskLens synthetic development dataset.

ALL records produced here are SIMULATED. Issuer and instrument names are
fictional and must not be mistaken for real investment opportunities.
Run:  python data/sample/generate.py
Output: data/sample/risklens_sample.json
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta

AS_OF = date(2025, 1, 15)
SIM = "SIMULATED"


def iso(d: date) -> str:
    return d.isoformat()


# --------------------------------------------------------------------------
# Issuers (all fictional)
# --------------------------------------------------------------------------
issuers = [
    {"id": "GOI-SIM", "name": "Republic Treasury (Simulated Sovereign)", "sector": "Sovereign", "is_government": True},
    {"id": "SDL-NR", "name": "Northern Region State Dev. Authority (Sim)", "sector": "Sovereign", "is_government": True},
    {"id": "SDL-SR", "name": "Southern Region State Dev. Authority (Sim)", "sector": "Sovereign", "is_government": True},
    {"id": "FINX", "name": "Finxora Capital Ltd (Simulated)", "sector": "Financials", "is_government": False},
    {"id": "INFRN", "name": "Infranova Projects Ltd (Simulated)", "sector": "Infrastructure", "is_government": False},
    {"id": "POWRD", "name": "Powergrid Dynamics Ltd (Simulated)", "sector": "Utilities", "is_government": False},
    {"id": "HOUSF", "name": "Housefirst Finance Ltd (Simulated)", "sector": "Financials", "is_government": False},
    {"id": "STEEL", "name": "Vajra Steelworks Ltd (Simulated)", "sector": "Materials", "is_government": False},
    {"id": "RETLX", "name": "Retailux Commerce Ltd (Simulated)", "sector": "Consumer", "is_government": False},
    {"id": "BANKA", "name": "Ashoka Commercial Bank (Simulated)", "sector": "Banking", "is_government": False},
    {"id": "BANKB", "name": "Meridian Co-op Bank (Simulated)", "sector": "Banking", "is_government": False},
    {"id": "AMC1", "name": "Trimurti Asset Managers (Simulated)", "sector": "Funds", "is_government": False},
]


# --------------------------------------------------------------------------
# Instrument builders
# --------------------------------------------------------------------------
instruments = []
bond_terms = []
credit_ratings = []
rating_history = []
market_prices = []
liquidity_metrics = []


def add_instrument(**kw):
    kw.setdefault("currency", "INR")
    kw.setdefault("data_status", SIM)
    instruments.append(kw)


def add_rating(instr_id, issuer_id, agency, symbol, rdate, outlook, action="Affirmed", prev=None):
    credit_ratings.append({
        "instrument_id": instr_id, "issuer_id": issuer_id, "agency": agency,
        "symbol": symbol, "rating_date": iso(rdate), "outlook": outlook,
        "action": action, "previous_symbol": prev, "data_status": SIM,
    })


def add_rating_history(instr_id, issuer_id, agency, entries):
    for symbol, rdate, action in entries:
        rating_history.append({
            "instrument_id": instr_id, "issuer_id": issuer_id, "agency": agency,
            "symbol": symbol, "rating_date": iso(rdate), "action": action, "data_status": SIM,
        })


def add_prices(instr_id, base_price, n=12):
    import math
    for i in range(n):
        d = AS_OF - timedelta(days=(n - 1 - i) * 7)
        wobble = math.sin(i / 2.0) * 0.4
        clean = round(base_price + wobble, 4)
        market_prices.append({
            "instrument_id": instr_id, "price_date": iso(d),
            "clean_price": clean, "source": "SIM-FEED", "data_status": SIM,
        })


def add_liquidity(instr_id, adtv, trading_days, spread_bps, depth, last_traded_offset):
    liquidity_metrics.append({
        "instrument_id": instr_id,
        "avg_daily_traded_value": adtv,
        "trading_days": trading_days,
        "window_days": 22,
        "bid_ask_spread_bps": spread_bps,
        "market_depth_value": depth,
        "last_traded_date": iso(AS_OF - timedelta(days=last_traded_offset)),
        "as_of_date": iso(AS_OF),
        "data_status": SIM,
    })


# ---- Government securities (G-Secs) ----
gsec_defs = [
    ("GS-SIM-068-2028", "Sim 6.80% GS 2028", 0.068, date(2028, 6, 1), 99.1, 2),
    ("GS-SIM-072-2031", "Sim 7.20% GS 2031", 0.072, date(2031, 9, 1), 100.3, 2),
    ("GS-SIM-074-2034", "Sim 7.40% GS 2034", 0.074, date(2034, 3, 1), 101.2, 2),
    ("GS-SIM-069-2040", "Sim 6.90% GS 2040", 0.069, date(2040, 1, 1), 95.8, 2),
    ("GS-SIM-076-2053", "Sim 7.60% GS 2053", 0.076, date(2053, 7, 1), 103.5, 2),
]
for iid, name, cpn, mat, price, freq in gsec_defs:
    add_instrument(id=iid, isin=f"SIM{iid[-6:]}G", name=name, category="G-Sec", issuer_id="GOI-SIM",
                   issue_date=iso(date(2021, 1, 1)), maturity_date=iso(mat), face_value=100.0,
                   min_investment=10000.0, coupon_rate=cpn, coupon_frequency=freq, day_count="ACT/ACT",
                   redemption_value=100.0, callable=False, puttable=False, secured=True, seniority="Senior",
                   listing_exchange="SIM-NDS", clean_price=price, is_government=True, sector="Sovereign")
    add_rating(iid, "GOI-SIM", "CRISIL", "SOV", date(2024, 12, 1), "Stable")
    add_prices(iid, price)
    add_liquidity(iid, 85_000_000, 22, 3, 25_000_000, 0)

# ---- Treasury Bills (zero-coupon) ----
tbill_defs = [
    ("TB-SIM-91D", "Sim 91-Day T-Bill", date(2025, 4, 10), 98.35),
    ("TB-SIM-182D", "Sim 182-Day T-Bill", date(2025, 7, 10), 96.60),
    ("TB-SIM-364D", "Sim 364-Day T-Bill", date(2026, 1, 10), 93.20),
]
for iid, name, mat, price in tbill_defs:
    add_instrument(id=iid, isin=f"SIM{iid[-5:]}T", name=name, category="T-Bill", issuer_id="GOI-SIM",
                   issue_date=iso(date(2024, 12, 1)), maturity_date=iso(mat), face_value=100.0,
                   min_investment=25000.0, coupon_rate=0.0, coupon_frequency=0, day_count="ACT/365F",
                   redemption_value=100.0, callable=False, puttable=False, secured=True, seniority="Senior",
                   listing_exchange="SIM-NDS", clean_price=price, is_government=True, sector="Sovereign")
    add_rating(iid, "GOI-SIM", "CRISIL", "SOV", date(2024, 12, 1), "Stable")
    add_prices(iid, price)
    add_liquidity(iid, 120_000_000, 22, 2, 30_000_000, 0)

# ---- State Development Loans ----
sdl_defs = [
    ("SDL-SIM-NR-2032", "Sim 7.45% Northern SDL 2032", 0.0745, date(2032, 5, 1), 100.1, "SDL-NR"),
    ("SDL-SIM-SR-2035", "Sim 7.55% Southern SDL 2035", 0.0755, date(2035, 8, 1), 100.6, "SDL-SR"),
    ("SDL-SIM-NR-2039", "Sim 7.62% Northern SDL 2039", 0.0762, date(2039, 2, 1), 100.9, "SDL-NR"),
]
for iid, name, cpn, mat, price, iss in sdl_defs:
    add_instrument(id=iid, isin=f"SIM{iid[-6:]}S", name=name, category="SDL", issuer_id=iss,
                   issue_date=iso(date(2022, 1, 1)), maturity_date=iso(mat), face_value=100.0,
                   min_investment=10000.0, coupon_rate=cpn, coupon_frequency=2, day_count="ACT/ACT",
                   redemption_value=100.0, callable=False, puttable=False, secured=True, seniority="Senior",
                   listing_exchange="SIM-NDS", clean_price=price, is_government=True, sector="Sovereign")
    add_rating(iid, iss, "ICRA", "AAA", date(2024, 11, 15), "Stable")
    add_prices(iid, price)
    add_liquidity(iid, 18_000_000, 16, 8, 6_000_000, 2)

# ---- Corporate bonds & NCDs ----
corp_defs = [
    # id, name, issuer, sector, coupon, maturity, price, freq, rating, agency, outlook, secured, callable, seniority
    ("NCD-SIM-FINX-2027", "Sim Finxora 8.60% Secured NCD 2027", "FINX", "Financials", 0.086, date(2027, 6, 15), 99.5, 2, "AA+", "CRISIL", "Stable", True, False, "Senior Secured"),
    ("NCD-SIM-FINX-2030", "Sim Finxora 9.10% Sub NCD 2030", "FINX", "Financials", 0.091, date(2030, 6, 15), 98.2, 2, "AA", "CRISIL", "Negative", False, False, "Subordinated"),
    ("NCD-SIM-INFRN-2029", "Sim Infranova 9.40% Secured NCD 2029", "INFRN", "Infrastructure", 0.094, date(2029, 3, 20), 100.0, 2, "A+", "CARE", "Stable", True, True, "Senior Secured"),
    ("NCD-SIM-INFRN-2033", "Sim Infranova 9.75% NCD 2033", "INFRN", "Infrastructure", 0.0975, date(2033, 3, 20), 97.0, 2, "A", "CARE", "Negative", False, False, "Senior"),
    ("BND-SIM-POWRD-2032", "Sim Powergrid Dyn. 8.20% Bond 2032", "POWRD", "Utilities", 0.082, date(2032, 10, 1), 100.4, 2, "AAA", "ICRA", "Stable", True, False, "Senior Secured"),
    ("NCD-SIM-HOUSF-2028", "Sim Housefirst 9.30% Secured NCD 2028", "HOUSF", "Financials", 0.093, date(2028, 9, 5), 99.0, 4, "AA-", "India Ratings", "Stable", True, False, "Senior Secured"),
    ("NCD-SIM-HOUSF-2031", "Sim Housefirst 9.85% NCD 2031", "HOUSF", "Financials", 0.0985, date(2031, 9, 5), 96.5, 2, "A+", "India Ratings", "Watch", False, True, "Senior"),
    ("NCD-SIM-STEEL-2029", "Sim Vajra Steel 10.25% NCD 2029", "STEEL", "Materials", 0.1025, date(2029, 11, 30), 95.2, 2, "BBB+", "CARE", "Negative", True, False, "Senior Secured"),
    ("NCD-SIM-STEEL-2027", "Sim Vajra Steel 10.60% Unsec NCD 2027", "STEEL", "Materials", 0.106, date(2027, 11, 30), 94.0, 2, "BBB", "CARE", "Negative", False, False, "Unsecured"),
    ("NCD-SIM-RETLX-2030", "Sim Retailux 11.10% NCD 2030", "RETLX", "Consumer", 0.111, date(2030, 4, 18), 93.0, 2, "BB+", "ICRA", "Negative", False, False, "Unsecured"),
]
for (iid, name, iss, sector, cpn, mat, price, freq, rat, ag, outlook, secured, callable_, seniority) in corp_defs:
    add_instrument(id=iid, isin=f"SIM{abs(hash(iid)) % 900000 + 100000}C", name=name, category="NCD",
                   issuer_id=iss, issue_date=iso(date(2022, 6, 15)), maturity_date=iso(mat), face_value=1000.0,
                   min_investment=10000.0, coupon_rate=cpn, coupon_frequency=freq, day_count="ACT/365F",
                   redemption_value=1000.0, callable=callable_, puttable=False, secured=secured, seniority=seniority,
                   listing_exchange="SIM-BSE", clean_price=price * 10.0, is_government=False, sector=sector,
                   call_date=iso(date(mat.year - 1, mat.month, mat.day)) if callable_ else None,
                   call_price=1010.0 if callable_ else None)
    add_rating(iid, iss, ag, rat, date(2024, 10, 1), outlook, action="Affirmed")
    add_prices(iid, price * 10.0)

# issuer-specific liquidity (lower for weaker/smaller names)
corp_liq = {
    "NCD-SIM-FINX-2027": (9_000_000, 14, 18, 3_000_000, 1),
    "NCD-SIM-FINX-2030": (4_000_000, 9, 35, 1_200_000, 4),
    "NCD-SIM-INFRN-2029": (3_500_000, 8, 45, 900_000, 5),
    "NCD-SIM-INFRN-2033": (1_800_000, 5, 70, 400_000, 9),
    "BND-SIM-POWRD-2032": (15_000_000, 18, 10, 5_000_000, 0),
    "NCD-SIM-HOUSF-2028": (5_000_000, 11, 28, 1_500_000, 2),
    "NCD-SIM-HOUSF-2031": (1_200_000, 4, 85, 300_000, 12),
    "NCD-SIM-STEEL-2029": (800_000, 3, 110, 200_000, 16),
    "NCD-SIM-STEEL-2027": (600_000, 2, 130, 150_000, 20),
    "NCD-SIM-RETLX-2030": (300_000, 1, 180, 80_000, 28),
}
for iid, (adtv, td, sp, dep, lo) in corp_liq.items():
    add_liquidity(iid, adtv, td, sp, dep, lo)

# downgrade rating history example for STEEL issuer
add_rating_history("NCD-SIM-STEEL-2029", "STEEL", "CARE", [
    ("A-", date(2022, 6, 15), "Assigned"),
    ("BBB+", date(2023, 9, 1), "Downgrade"),
])

# ---- Bank Fixed Deposits ----
fd_defs = [
    ("FD-SIM-BANKA-CUM-3Y", "Sim Ashoka Bank 7.50% Cumulative FD 3Y", "BANKA", 0.075, date(2028, 1, 15), True, "AAA", "CRISIL"),
    ("FD-SIM-BANKA-NC-5Y", "Sim Ashoka Bank 7.65% Non-Cum FD 5Y", "BANKA", 0.0765, date(2030, 1, 15), False, "AAA", "CRISIL"),
    ("FD-SIM-BANKB-CUM-2Y", "Sim Meridian Co-op 8.10% Cumulative FD 2Y", "BANKB", 0.081, date(2027, 1, 15), True, "AA", "ICRA"),
    ("FD-SIM-BANKB-NC-3Y", "Sim Meridian Co-op 8.25% Non-Cum FD 3Y", "BANKB", 0.0825, date(2028, 1, 15), False, "AA", "ICRA"),
    ("FD-SIM-BANKA-TAX-5Y", "Sim Ashoka Bank 7.40% Tax-Saver FD 5Y", "BANKA", 0.074, date(2030, 1, 15), True, "AAA", "CRISIL"),
]
for iid, name, iss, rate, mat, cumulative, rat, ag in fd_defs:
    add_instrument(id=iid, isin=None, name=name, category="FD", issuer_id=iss,
                   issue_date=iso(date(2025, 1, 15)), maturity_date=iso(mat), face_value=100000.0,
                   min_investment=10000.0, coupon_rate=rate,
                   coupon_frequency=0 if cumulative else 4, day_count="ACT/365F",
                   redemption_value=100000.0, callable=False, puttable=True, secured=False,
                   seniority="Deposit", listing_exchange=None, clean_price=100000.0,
                   is_government=False, sector="Banking", cumulative=cumulative)
    add_rating(iid, iss, ag, rat, date(2024, 12, 20), "Stable")
    # FDs are not exchange traded -> no secondary liquidity
    add_liquidity(iid, None, None, None, None, 0)

# ---- Debt Mutual Funds ----
mf_defs = [
    ("MF-SIM-LIQ", "Sim Trimurti Liquid Fund", 0.0710, 0.1, "Liquid", 95),
    ("MF-SIM-USD", "Sim Trimurti Ultra Short Duration Fund", 0.0745, 0.6, "Ultra-Short", 80),
    ("MF-SIM-CORP", "Sim Trimurti Corporate Bond Fund", 0.0790, 2.8, "Corporate Bond", 65),
    ("MF-SIM-GILT", "Sim Trimurti Gilt Fund", 0.0730, 6.2, "Gilt", 70),
    ("MF-SIM-TMF2030", "Sim Trimurti Target Maturity 2030 Fund", 0.0775, 4.5, "Target Maturity", 60),
]
for iid, name, ytm, dur, kind, liq in mf_defs:
    add_instrument(id=iid, isin=None, name=name, category="Debt MF", issuer_id="AMC1",
                   issue_date=iso(date(2023, 1, 1)), maturity_date=None, face_value=None,
                   min_investment=5000.0, coupon_rate=0.0, coupon_frequency=0, day_count=None,
                   redemption_value=None, callable=False, puttable=True, secured=False,
                   seniority=None, listing_exchange=None, clean_price=None, nav=round(10 + ytm * 50, 4),
                   is_government=False, sector="Funds", fund_kind=kind,
                   indicative_ytm=ytm, indicative_duration=dur)
    add_rating(iid, "AMC1", "CRISIL", "AAA", date(2024, 12, 1), "Stable", action="Fund Credit Quality")
    add_liquidity(iid, None, None, None, None, 0)  # open-ended; redeem at NAV

# --------------------------------------------------------------------------
# Sample issuer news
# --------------------------------------------------------------------------
news = [
    {"headline": "Sim: Vajra Steelworks reports weaker Q3 margins", "issuer_id": "STEEL",
     "instrument_ids": ["NCD-SIM-STEEL-2029", "NCD-SIM-STEEL-2027"], "category": "Quarterly Results",
     "published_at": iso(AS_OF - timedelta(days=3)), "source": "SIM-DISCLOSURE",
     "summary": "Simulated: issuer reported margin compression; watch for leverage impact.",
     "risk_impact": "High", "relevance": 0.85, "data_status": SIM},
    {"headline": "Sim: CARE revises Vajra Steelworks outlook to Negative", "issuer_id": "STEEL",
     "instrument_ids": ["NCD-SIM-STEEL-2029"], "category": "Rating Downgrade",
     "published_at": iso(AS_OF - timedelta(days=10)), "source": "SIM-RATING-AGENCY",
     "summary": "Simulated: outlook revised to Negative citing cash-flow pressure.",
     "risk_impact": "Critical", "relevance": 0.95, "data_status": SIM},
    {"headline": "Sim: Housefirst Finance raises fresh capital", "issuer_id": "HOUSF",
     "instrument_ids": ["NCD-SIM-HOUSF-2028", "NCD-SIM-HOUSF-2031"], "category": "Fundraising",
     "published_at": iso(AS_OF - timedelta(days=6)), "source": "SIM-EXCHANGE-FILING",
     "summary": "Simulated: equity raise improves capital adequacy.",
     "risk_impact": "Informational", "relevance": 0.6, "data_status": SIM},
    {"headline": "Sim: RBI policy holds repo rate steady", "issuer_id": "GOI-SIM",
     "instrument_ids": [], "category": "RBI Announcement",
     "published_at": iso(AS_OF - timedelta(days=1)), "source": "SIM-CENTRAL-BANK",
     "summary": "Simulated: policy rate unchanged; stance neutral.",
     "risk_impact": "Medium", "relevance": 0.5, "data_status": SIM},
    {"headline": "Sim: Retailux Commerce faces litigation claim", "issuer_id": "RETLX",
     "instrument_ids": ["NCD-SIM-RETLX-2030"], "category": "Litigation",
     "published_at": iso(AS_OF - timedelta(days=12)), "source": "SIM-DISCLOSURE",
     "summary": "Simulated: contingent liability disclosed; monitor resolution.",
     "risk_impact": "High", "relevance": 0.8, "data_status": SIM},
]


# --------------------------------------------------------------------------
# Sample investor portfolios (holdings reference instruments above)
# --------------------------------------------------------------------------
portfolios = [
    {
        "name": "Sim Conservative Income",
        "description": "SIMULATED sample portfolio — government-heavy, high liquidity.",
        "holdings": [
            {"instrument_id": "GS-SIM-068-2028", "quantity": 5000, "buy_price": 98.9, "buy_date": "2024-07-01"},
            {"instrument_id": "GS-SIM-072-2031", "quantity": 4000, "buy_price": 100.1, "buy_date": "2024-08-15"},
            {"instrument_id": "TB-SIM-364D", "quantity": 3000, "buy_price": 92.8, "buy_date": "2024-12-05"},
            {"instrument_id": "BND-SIM-POWRD-2032", "quantity": 300, "buy_price": 1002.0, "buy_date": "2024-09-10"},
            {"instrument_id": "FD-SIM-BANKA-CUM-3Y", "quantity": 1, "buy_price": 100000.0, "buy_date": "2025-01-15"},
        ],
    },
    {
        "name": "Sim Balanced Yield",
        "description": "SIMULATED sample portfolio — mix of sovereign and corporate credit.",
        "holdings": [
            {"instrument_id": "GS-SIM-074-2034", "quantity": 3000, "buy_price": 100.8, "buy_date": "2024-06-20"},
            {"instrument_id": "SDL-SIM-SR-2035", "quantity": 2000, "buy_price": 100.2, "buy_date": "2024-10-01"},
            {"instrument_id": "NCD-SIM-FINX-2027", "quantity": 500, "buy_price": 995.0, "buy_date": "2024-11-11"},
            {"instrument_id": "NCD-SIM-HOUSF-2028", "quantity": 400, "buy_price": 988.0, "buy_date": "2024-12-01"},
            {"instrument_id": "NCD-SIM-STEEL-2029", "quantity": 300, "buy_price": 960.0, "buy_date": "2024-09-25"},
            {"instrument_id": "MF-SIM-CORP", "quantity": 2000, "buy_price": 13.9, "buy_date": "2024-05-02"},
        ],
    },
]


def main():
    out = {
        "_meta": {
            "status": SIM,
            "as_of": iso(AS_OF),
            "note": "All issuers, instruments, prices, ratings, liquidity and news are FICTIONAL and SIMULATED.",
            "counts": {
                "issuers": len(issuers), "instruments": len(instruments),
                "ratings": len(credit_ratings), "prices": len(market_prices),
                "liquidity": len(liquidity_metrics), "news": len(news),
                "portfolios": len(portfolios),
            },
        },
        "issuers": issuers,
        "instruments": instruments,
        "credit_ratings": credit_ratings,
        "rating_history": rating_history,
        "market_prices": market_prices,
        "liquidity_metrics": liquidity_metrics,
        "news": news,
        "portfolios": portfolios,
    }
    path = os.path.join(os.path.dirname(__file__), "risklens_sample.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {path}")
    print("Instrument count:", len(instruments))


if __name__ == "__main__":
    main()
