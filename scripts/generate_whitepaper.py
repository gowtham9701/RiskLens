"""Generate the RiskLens project whitepaper PDF.

Run (venv active):  python scripts/generate_whitepaper.py
Output:             docs/RiskLens_Whitepaper.pdf

Reproducible, versioned generator so the PDF can be rebuilt from source.
"""

from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#1f2a44")
ACCENT = colors.HexColor("#2f6f4f")
GREY = colors.HexColor("#5b6472")
LIGHT = colors.HexColor("#eef1f6")

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "RiskLens_Whitepaper.pdf")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("CoverTitle", parent=ss["Title"], fontSize=30, textColor=NAVY, leading=34))
    ss.add(ParagraphStyle("CoverSub", parent=ss["Normal"], fontSize=13, textColor=GREY,
                          alignment=TA_CENTER, leading=18))
    ss.add(ParagraphStyle("H1", parent=ss["Heading1"], textColor=NAVY, fontSize=16, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], textColor=ACCENT, fontSize=12.5, spaceBefore=10, spaceAfter=4))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=10.3, leading=15, alignment=TA_JUSTIFY, spaceAfter=6))
    ss.add(ParagraphStyle("RLBullet", parent=ss["Normal"], fontSize=10.3, leading=14))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=8.5, textColor=GREY, leading=11))
    ss.add(ParagraphStyle("TblH", parent=ss["Normal"], fontSize=9.5, textColor=colors.white, leading=12))
    ss.add(ParagraphStyle("TblC", parent=ss["Normal"], fontSize=9.2, leading=12))
    return ss


S = _styles()


def para(t, style="Body"):
    return Paragraph(t, S[style])


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(i, S["RLBullet"]), leftIndent=10) for i in items],
        bulletType="bullet", start="•", leftIndent=12, spaceAfter=6,
    )


def table(rows, col_widths, header=True):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7cdd8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    t.setStyle(TableStyle(style))
    return t


def hr():
    return HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#c7cdd8"),
                      spaceBefore=6, spaceAfter=6)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    if doc.page > 1:
        canvas.drawString(2 * cm, 1.1 * cm, "RiskLens — Project Whitepaper")
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.drawCentredString(A4[0] / 2, 1.1 * cm, "SIMULATED DATA · Not investment advice")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(OUT, pagesize=A4, title="RiskLens — Project Whitepaper",
                            author="RiskLens", leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=1.8 * cm)
    e = []

    # ---------- Cover ----------
    e += [Spacer(1, 3.5 * cm)]
    e += [para("RiskLens", "CoverTitle")]
    e += [Spacer(1, 0.3 * cm)]
    e += [para("Fixed-Income Intelligence, Portfolio Optimisation &amp; Risk Analytics Platform", "CoverSub")]
    e += [Spacer(1, 0.2 * cm)]
    e += [para("India-focused MVP · Project Whitepaper", "CoverSub")]
    e += [Spacer(1, 1.2 * cm)]
    e += [table([
        [Paragraph("Product", S["TblC"]), Paragraph("RiskLens — fixed-income analytics &amp; decision-support", S["TblC"])],
        [Paragraph("Market", S["TblC"]), Paragraph("India (extensible to other markets)", S["TblC"])],
        [Paragraph("Users", S["TblC"]), Paragraph("Individual investors &amp; investment professionals", S["TblC"])],
        [Paragraph("Stack", S["TblC"]), Paragraph("Next.js · FastAPI · SQLAlchemy · PostgreSQL · NumPy/SciPy", S["TblC"])],
        [Paragraph("Repository", S["TblC"]), Paragraph("github.com/gowtham9701/RiskLens", S["TblC"])],
        [Paragraph("Date", S["TblC"]), Paragraph(date.today().strftime("%d %B %Y"), S["TblC"])],
    ], [4 * cm, 11 * cm], header=False)]
    e += [Spacer(1, 1.5 * cm)]
    e += [para("<b>Disclaimer.</b> All bundled data is SIMULATED. RiskLens is an analytics and "
               "decision-support tool. It does not provide investment advice and does not guarantee "
               "returns, capital protection, liquidity or credit quality. Yields, liquidity scores and "
               "stress results are indicative estimates only.", "Small")]
    e += [PageBreak()]

    # ---------- Executive summary ----------
    e += [para("1. Executive Summary", "H1"), hr()]
    e += [para(
        "RiskLens is a full-stack platform that helps individuals and professionals discover, value, "
        "construct, optimise and monitor fixed-income portfolios across Indian instrument classes — "
        "Government Securities, Treasury Bills, State Development Loans, corporate bonds/NCDs, bank "
        "fixed deposits and debt mutual funds. It pairs an institutional-grade, independently tested "
        "financial engine with a transparent, never-fabricate-data philosophy: every figure is "
        "traceable to a source and timestamp, and nothing is presented as a guarantee.")]
    e += [para(
        "The platform answers the core investor question — <i>is the extra yield worth the risk, and how "
        "do I build and watch a portfolio around it?</i> — through risk-adjusted analytics (duration, "
        "convexity, DV01), a transparent 0–100 liquidity score, a cash-flow-weighted portfolio yield, a "
        "SciPy constrained optimiser, scenario stress testing, and proactive alerts.")]

    # ---------- Business idea ----------
    e += [para("2. Business Idea", "H1"), hr()]
    e += [para(
        "India's fixed-income market is large and increasingly accessible to retail investors via RBI "
        "Retail Direct, online bond platforms and debt mutual funds. The tools to <i>evaluate</i> these "
        "instruments, however, remain fragmented, spreadsheet-driven and skewed toward institutions. "
        "RiskLens provides a single, transparent intelligence layer positioned explicitly as analytics "
        "and decision-support — not a broker and not an advisor.")]
    e += [para("Value proposition", "H2")]
    e += [bullets([
        "<b>Risk-adjusted transparency</b> — every yield is shown next to its credit, liquidity and "
        "interest-rate risk, with the methodology exposed.",
        "<b>Correct financial maths</b> — cash-flow-weighted portfolio yield and instrument-specific "
        "methods, avoiding the common errors in consumer tools.",
        "<b>Actionable construction &amp; monitoring</b> — constraint-based portfolio building, stress "
        "testing, cash-flow laddering and event alerts in one place.",
        "<b>Extensible &amp; provider-agnostic</b> — data adapters can be swapped without touching the "
        "calculation engine; new instrument classes and markets can be added.",
    ])]

    # ---------- Problem ----------
    e += [para("3. Problem Statement", "H1"), hr()]
    e += [table([
        [Paragraph("<b>Challenge</b>", S["TblH"]), Paragraph("<b>Why it hurts investors</b>", S["TblH"])],
        [Paragraph("Yield ≠ safety", S["TblC"]), Paragraph("Higher coupons often hide credit, liquidity or duration risk retail tools never surface.", S["TblC"])],
        [Paragraph("Fragmented data", S["TblC"]), Paragraph("Prices, ratings, secondary-market liquidity and issuer news live in separate silos.", S["TblC"])],
        [Paragraph("Opaque liquidity", S["TblC"]), Paragraph("Investors confuse large issue size with the real ability to sell; many bonds barely trade.", S["TblC"])],
        [Paragraph("Wrong maths", S["TblC"]), Paragraph("Averaging individual YTMs is incorrect; bond formulas are wrongly applied to FDs/funds.", S["TblC"])],
        [Paragraph("No portfolio view", S["TblC"]), Paragraph("Little support for constrained construction, laddering, stress testing or downgrade impact.", S["TblC"])],
        [Paragraph("Reactive monitoring", S["TblC"]), Paragraph("Downgrades and liquidity deterioration are discovered too late.", S["TblC"])],
    ], [5 * cm, 10 * cm])]

    # ---------- Solution ----------
    e += [para("4. Solution Provided by RiskLens", "H1"), hr()]
    e += [table([
        [Paragraph("<b>Problem</b>", S["TblH"]), Paragraph("<b>RiskLens solution</b>", S["TblH"])],
        [Paragraph("Yield ≠ safety", S["TblC"]), Paragraph("Duration, convexity, DV01, credit &amp; liquidity scoring shown beside every yield.", S["TblC"])],
        [Paragraph("Fragmented data", S["TblC"]), Paragraph("One data model unifying instruments, prices, ratings, liquidity, news &amp; issuers.", S["TblC"])],
        [Paragraph("Opaque liquidity", S["TblC"]), Paragraph("Transparent 0–100 liquidity score (5 weighted components) + estimated liquidation days/cost.", S["TblC"])],
        [Paragraph("Wrong maths", S["TblC"]), Paragraph("Cash-flow-weighted portfolio YTM (IRR); instrument-specific methods for FDs &amp; funds.", S["TblC"])],
        [Paragraph("No portfolio view", S["TblC"]), Paragraph("SciPy constrained optimiser, maturity ladder, stress testing, cash-flow calendar.", S["TblC"])],
        [Paragraph("Reactive monitoring", S["TblC"]), Paragraph("Alerts for downgrades, negative outlooks, liquidity drops, concentration &amp; maturities.", S["TblC"])],
    ], [5 * cm, 10 * cm])]
    e += [Spacer(1, 4)]
    e += [para("<b>Core principle:</b> maximise income/yield <i>subject to transparent risk constraints</i>, "
               "and always disclose data sources, timestamps, assumptions and limitations.")]

    # ---------- Target users ----------
    e += [para("5. Target Users", "H1"), hr()]
    e += [para("Individual investors", "H2")]
    e += [bullets([
        "Enter budget, horizon and income needs; receive a clear proposed portfolio.",
        "Compare alternatives, track income and maturities, and receive relevant alerts.",
        "Interface understandable without professional financial knowledge.",
    ])]
    e += [para("Investment professionals", "H2")]
    e += [bullets([
        "Detailed bond valuation, portfolio YTM, duration/convexity/DV01, rating migration.",
        "Historical liquidity analytics, stress testing, data-quality monitoring and audit trails.",
        "Multiple portfolios, performance attribution, and Excel/PDF reporting.",
    ])]

    e += [PageBreak()]

    # ---------- Architecture ----------
    e += [para("6. System Architecture", "H1"), hr()]
    e += [para(
        "RiskLens is a modular monorepo with a strict separation between the financial calculation "
        "engine, the application backend, data ingestion and the UI. The engine is a standalone, "
        "independently unit-tested Python package with no web or database dependencies, ensuring the "
        "maths is correct regardless of data provider.")]
    e += [table([
        [Paragraph("<b>Layer</b>", S["TblH"]), Paragraph("<b>Technology</b>", S["TblH"]), Paragraph("<b>Responsibility</b>", S["TblH"])],
        [Paragraph("Frontend", S["TblC"]), Paragraph("Next.js, TypeScript, Tailwind, Plotly", S["TblC"]), Paragraph("Dashboards, explore, builder, risk, reports", S["TblC"])],
        [Paragraph("Backend", S["TblC"]), Paragraph("FastAPI, Pydantic, SQLAlchemy, JWT", S["TblC"]), Paragraph("REST API, auth, user-scoped portfolios", S["TblC"])],
        [Paragraph("Analytics", S["TblC"]), Paragraph("NumPy, SciPy, pandas", S["TblC"]), Paragraph("Pricing, yield, risk, liquidity, optimiser, stress", S["TblC"])],
        [Paragraph("Database", S["TblC"]), Paragraph("PostgreSQL (29 tables, NUMERIC)", S["TblC"]), Paragraph("Normalised, precise, user-isolated storage", S["TblC"])],
        [Paragraph("Reporting", S["TblC"]), Paragraph("OpenPyXL, ReportLab", S["TblC"]), Paragraph("Excel &amp; PDF portfolio reports", S["TblC"])],
        [Paragraph("Deploy", S["TblC"]), Paragraph("Docker, Render, Vercel, Neon, CI", S["TblC"]), Paragraph("Reproducible build &amp; cloud deployment", S["TblC"])],
    ], [2.6 * cm, 5.4 * cm, 7 * cm])]

    # ---------- Modules ----------
    e += [para("7. Application Modules", "H1"), hr()]
    e += [bullets([
        "<b>Executive Dashboard</b> — value, gain/loss, weighted yield, income, duration, DV01, allocations, maturity ladder.",
        "<b>Instrument Database</b> — master records with full terms, prices, ratings, day-count schedules.",
        "<b>Calculation Engine</b> — valuation, cash-flow generation, yield-curve shifts.",
        "<b>Credit Intelligence</b> — rating history, outlooks, downgrade alerts with portfolio impact.",
        "<b>Liquidity Intelligence</b> — volume analysis, spread/depth tracking, illiquidity flags.",
        "<b>News &amp; Events</b> — issuer/instrument-linked disclosures with summaries (LLM-ready).",
        "<b>Portfolio Builder</b> — questionnaire + SciPy optimiser producing compliant target portfolios.",
        "<b>Risk &amp; Stress Testing</b> — rate/spread shifts, downgrades, default-recovery, liquidity shocks.",
        "<b>Cash-Flow Calendar</b> — coupons, FD interest, maturities, reinvestment needs.",
        "<b>Portfolio Management</b> — multi-portfolio, transactions, CSV import, attribution.",
        "<b>Alerts</b> — downgrades, negative outlooks, liquidity drops, maturity &amp; concentration risks.",
        "<b>Reporting &amp; Data Quality</b> — PDF/Excel export + exception tracking console.",
    ])]

    e += [PageBreak()]

    # ---------- Methodology ----------
    e += [para("8. Financial Methodology (highlights)", "H1"), hr()]
    e += [bullets([
        "<b>Day counts</b>: ACT/365F, ACT/360, ACT/ACT, 30/360, 30E/360.",
        "<b>Pricing &amp; yield</b>: present value, clean/dirty price, YTM/YTC/YTP (Brent solver), zero-coupon &amp; current yield.",
        "<b>Risk</b>: Macaulay &amp; modified duration, convexity, DV01, effective duration; first+second order price change.",
        "<b>Portfolio</b>: cash-flow-weighted YTM (IRR of aggregated flows) — never a naive average; XIRR; weighted duration/DV01.",
        "<b>Liquidity score</b>: ADTV 25%, trading frequency 20%, spread 20%, depth 20%, recency 15%; 'Insufficient data' when sparse.",
        "<b>Optimiser</b>: SciPy SLSQP; hard constraints on credit, liquidity, duration, issuer/sector caps, ticket size; reports infeasibility.",
        "<b>Stress</b>: ±50/±100 bps rate &amp; spread shocks, downgrade, default-with-recovery, volume drop, forced liquidation.",
    ])]
    e += [para("Validated by 30 analytics unit tests (par/premium/discount pricing, YTM round-trips, "
               "zero-coupon duration = maturity, DV01 ≈ ModDur·P·1bp, optimiser constraints) and 15 API "
               "integration tests. All monetary/yield values are stored as SQL NUMERIC, never float.")]

    # ---------- Data integrity & security ----------
    e += [para("9. Data Integrity, Security &amp; Controls", "H1"), hr()]
    e += [bullets([
        "Provider-agnostic adapters; synthetic-data mode by default; manual CSV import path.",
        "Data-quality validations: duplicates, missing/stale prices, invalid maturities, allocation totals.",
        "bcrypt password hashing, JWT auth, strict per-user portfolio isolation, parameterised ORM queries.",
        "Secrets only in environment variables; audit-log and data-exception tables for traceability.",
        "Graceful degradation: a news/LLM outage never blocks portfolio calculations.",
    ])]

    # ---------- End-to-end guide ----------
    e += [para("10. End-to-End Project Guide", "H1"), hr()]
    e += [para("Local run (no Docker)", "H2")]
    e += [table([
        [Paragraph("<b>Step</b>", S["TblH"]), Paragraph("<b>Command</b>", S["TblH"])],
        [Paragraph("Create venv", S["TblC"]), Paragraph("python3 -m venv .venv &amp;&amp; source .venv/bin/activate", S["TblC"])],
        [Paragraph("Install engine", S["TblC"]), Paragraph("pip install -e ./analytics", S["TblC"])],
        [Paragraph("Install backend", S["TblC"]), Paragraph("pip install -r backend/requirements.txt", S["TblC"])],
        [Paragraph("Configure", S["TblC"]), Paragraph("cp .env.example .env  (set DATABASE_URL or use SQLite)", S["TblC"])],
        [Paragraph("Seed data", S["TblC"]), Paragraph("python -m backend.app.seed", S["TblC"])],
        [Paragraph("Run API", S["TblC"]), Paragraph("uvicorn backend.app.main:app --reload --port 8000", S["TblC"])],
        [Paragraph("Run UI", S["TblC"]), Paragraph("cd frontend &amp;&amp; npm install &amp;&amp; npm run dev", S["TblC"])],
        [Paragraph("Run tests", S["TblC"]), Paragraph("pytest analytics/tests backend/tests -q", S["TblC"])],
    ], [3.4 * cm, 11.6 * cm])]
    e += [Spacer(1, 4)]
    e += [para("Demo login: <b>demo@risklens.sim / demo1234</b>. API docs at /docs.", "Small")]
    e += [para("Cloud deployment", "H2")]
    e += [bullets([
        "<b>Database</b>: Neon (or Supabase / Render Postgres) — copy the connection string.",
        "<b>Backend</b>: Render Blueprint (render.yaml) — set DATABASE_URL &amp; CORS_ORIGINS; seeds only if empty.",
        "<b>Frontend</b>: Vercel — Root Directory = frontend, set NEXT_PUBLIC_API_URL to the backend URL.",
        "<b>Alternatives</b>: Railway, Fly.io, Google Cloud Run, Koyeb (backend); Netlify, Cloudflare Pages (frontend); Coolify/Dokku/CapRover (self-host).",
    ])]

    # ---------- Roadmap & limitations ----------
    e += [para("11. Roadmap &amp; Known Limitations", "H1"), hr()]
    e += [bullets([
        "All bundled data is simulated; live market/rating/news feeds require licences &amp; credentials.",
        "QuantLib, option-adjusted (OAS) pricing, key-rate durations and TWR are future enhancements.",
        "Performance: add query-batching + Redis caching and background ingestion for scale.",
        "Hardening: refresh-token rotation, full rate-limiting, and Alembic migrations before launch.",
        "Regulatory review (securities, investment-advice, data-licensing, privacy) required pre-commercial.",
    ])]

    # ---------- Disclaimer ----------
    e += [para("12. Legal &amp; Financial Disclaimer", "H1"), hr()]
    e += [para(
        "RiskLens is an investment analytics and decision-support platform. It must not be used as a "
        "substitute for professional investment advice. It does not guarantee returns or capital "
        "protection, does not treat ratings or secured status as risk-free, and presents estimated "
        "liquidity and indicative yields as estimates, not guarantees. All bundled data is simulated and "
        "clearly labelled. Review applicable Indian securities, investment-advice, data-licensing, "
        "privacy and consumer-protection requirements before any commercial use.")]

    doc.build(e, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
