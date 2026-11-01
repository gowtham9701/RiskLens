"""Excel (OpenPyXL) and PDF (ReportLab) report generation."""

from __future__ import annotations

import io
from datetime import date

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from ..models import Portfolio
from . import portfolio_service as ps

DISCLAIMER = (
    "SIMULATED DATA — RiskLens is an analytics and decision-support tool. "
    "Figures are indicative, not guaranteed returns or investment advice."
)


def portfolio_excel(db: Session, portfolio: Portfolio) -> bytes:
    dash = ps.dashboard(db, portfolio.id)
    risk = ps.portfolio_risk(db, portfolio.id)
    wb = Workbook()

    ws = wb.active
    ws.title = "Summary"
    ws.append(["RiskLens Portfolio Report (SIMULATED)"])
    ws.append(["Portfolio", portfolio.name])
    ws.append(["As of", dash["as_of"]])
    ws.append([])
    ws.append(["KPI", "Value"])
    for k, v in dash["kpis"].items():
        ws.append([k, v])
    ws.append([])
    ws.append([DISCLAIMER])

    wh = wb.create_sheet("Holdings")
    wh.append(["Instrument", "Category", "Issuer", "Market Value", "YTM",
               "Mod Duration", "Rating", "Liquidity"])
    for h in dash["positions"]:
        wh.append([h["name"], h["category"], h["issuer_name"], h["market_value"],
                   h["ytm"], h["modified_duration"], h["rating"], h["liquidity_class"]])

    wa = wb.create_sheet("Allocation")
    wa.append(["Dimension", "Label", "Value", "Pct"])
    for dim, key in [("Category", "allocation_category"), ("Rating", "allocation_rating"),
                     ("Issuer", "allocation_issuer"), ("Liquidity", "liquidity_buckets")]:
        for row in dash[key]:
            wa.append([dim, row["label"], row["value"], row["pct"]])

    wr = wb.create_sheet("Stress")
    wr.append(["Scenario", "Description", "P&L", "P&L %"])
    for s in risk["stress"]:
        wr.append([s["name"], s["description"], s["pnl"], s["pnl_pct"]])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def portfolio_pdf(db: Session, portfolio: Portfolio) -> bytes:
    dash = ps.dashboard(db, portfolio.id)
    risk = ps.portfolio_risk(db, portfolio.id)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="RiskLens Portfolio Report")
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("RiskLens Portfolio Report", styles["Title"]))
    elems.append(Paragraph(f"Portfolio: {portfolio.name} &mdash; As of {dash['as_of']}", styles["Normal"]))
    elems.append(Paragraph(f"<b>{DISCLAIMER}</b>", styles["Normal"]))
    elems.append(Spacer(1, 12))

    kpi_rows = [["KPI", "Value"]] + [[k, str(v)] for k, v in dash["kpis"].items()]
    t = Table(kpi_rows, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2a44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elems.append(Paragraph("Portfolio KPIs", styles["Heading2"]))
    elems.append(t)
    elems.append(Spacer(1, 12))

    hold_rows = [["Instrument", "Cat", "MV", "YTM", "Dur", "Rating"]]
    for h in dash["positions"]:
        hold_rows.append([h["name"][:28], h["category"], f'{h["market_value"]:.0f}',
                          f'{(h["ytm"] or 0):.2%}', f'{h["modified_duration"] or 0:.1f}',
                          h["rating"] or "-"])
    th = Table(hold_rows, hAlign="LEFT")
    th.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2a44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elems.append(Paragraph("Holdings", styles["Heading2"]))
    elems.append(th)
    elems.append(Spacer(1, 12))

    stress_rows = [["Scenario", "P&L", "P&L %"]]
    for s in risk["stress"]:
        stress_rows.append([s["name"], f'{s["pnl"]:.0f}', f'{s["pnl_pct"]:.2%}'])
    ts = Table(stress_rows, hAlign="LEFT")
    ts.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7a1f1f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elems.append(Paragraph("Stress Testing", styles["Heading2"]))
    elems.append(ts)
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(risk["disclaimer"], styles["Italic"]))

    doc.build(elems)
    return buf.getvalue()
