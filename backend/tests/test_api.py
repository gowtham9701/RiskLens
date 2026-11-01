"""Integration tests for the RiskLens API."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "t1@risklens.sim", "password": "secret1", "full_name": "T1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "t1@risklens.sim"


def test_login_bad_password(client):
    assert client.post("/auth/login", json={"email": "demo@risklens.sim", "password": "wrong"}).status_code == 401


def test_requires_auth(client):
    assert client.get("/portfolios").status_code == 401


def test_instruments_list_and_detail(client):
    r = client.get("/instruments?page_size=5")
    body = r.json()
    assert r.status_code == 200
    assert body["total"] >= 30
    assert len(body["items"]) == 5
    iid = "GS-SIM-068-2028"
    d = client.get(f"/instruments/{iid}").json()
    assert d["ytm"] is not None
    assert d["modified_duration"] is not None
    assert d["data_status"] == "SIMULATED"


def test_instrument_filter_category(client):
    r = client.get("/instruments?category=T-Bill")
    cats = {i["category"] for i in r.json()["items"]}
    assert cats == {"T-Bill"}


def test_calculation_par_bond(client):
    r = client.post("/calculations/bond-price", json={
        "issue_date": "2020-01-01", "maturity_date": "2030-01-01", "coupon_rate": 0.05,
        "frequency": 1, "yield": 0.05, "settlement_date": "2020-01-01",
        "face_value": 100, "day_count": "30/360",
    })
    assert abs(r.json()["clean_price"] - 100.0) < 1e-6


def test_portfolio_dashboard(client, auth_headers):
    pid = client.get("/portfolios", headers=auth_headers).json()["items"][0]["id"]
    d = client.get(f"/portfolios/{pid}/dashboard", headers=auth_headers).json()
    kpis = d["kpis"]
    assert kpis["holdings"] >= 1
    assert kpis["market_value"] > 0
    # cash-flow-weighted yield, not a naive average
    assert kpis["weighted_yield"] is not None
    assert d["allocation_category"]


def test_portfolio_risk_stress(client, auth_headers):
    pid = client.get("/portfolios", headers=auth_headers).json()["items"][0]["id"]
    risk = client.get(f"/portfolios/{pid}/risk", headers=auth_headers).json()
    names = {s["name"] for s in risk["stress"]}
    assert "Rates +100bps" in names
    up = next(s for s in risk["stress"] if s["name"] == "Rates +100bps")
    assert up["pnl"] < 0  # rate rise => mark-to-market loss


def test_create_portfolio_and_add_holding(client, auth_headers):
    pid = client.post("/portfolios", json={"name": "Test PF", "description": "x"}, headers=auth_headers).json()["id"]
    r = client.post(f"/portfolios/{pid}/holdings",
                    json={"instrument_id": "GS-SIM-072-2031", "quantity": 1000,
                          "buy_price": 100.0, "buy_date": "2024-06-01"}, headers=auth_headers)
    assert r.status_code == 200
    detail = client.get(f"/portfolios/{pid}", headers=auth_headers).json()
    assert detail["holdings"][0]["instrument_id"] == "GS-SIM-072-2031"


def test_cross_user_isolation(client):
    # new user cannot see demo's portfolios
    tok = client.post("/auth/register", json={"email": "iso@risklens.sim", "password": "secret1"}).json()["access_token"]
    items = client.get("/portfolios", headers={"Authorization": f"Bearer {tok}"}).json()["items"]
    assert items == []


def test_builder_feasible(client, auth_headers):
    r = client.post("/portfolio-builder/generate", json={
        "amount": 1_000_000, "objective": "max_yield",
        "constraints": {"max_issuer_weight": 0.3, "max_sector_weight": 0.5,
                        "max_weight_per_instrument": 0.25, "max_duration": 7},
    }, headers=auth_headers)
    body = r.json()
    assert body["feasible"] is True
    assert abs(sum(a["weight"] for a in body["allocations"]) - 1.0) < 1e-3
    for a in body["allocations"]:
        assert a["weight"] <= 0.25 + 1e-6


def test_builder_infeasible(client, auth_headers):
    r = client.post("/portfolio-builder/generate", json={
        "amount": 1_000_000, "objective": "max_yield",
        "constraints": {"min_government_weight": 0.9, "max_sector_weight": 0.1},
    }, headers=auth_headers)
    body = r.json()
    assert body["feasible"] is False
    assert body["infeasible_reasons"]


def test_reports_download(client, auth_headers):
    pid = client.get("/portfolios", headers=auth_headers).json()["items"][0]["id"]
    xlsx = client.get(f"/reports/portfolio/{pid}?format=xlsx", headers=auth_headers)
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"  # xlsx is a zip
    pdf = client.get(f"/reports/portfolio/{pid}?format=pdf", headers=auth_headers)
    assert pdf.content[:4] == b"%PDF"


def test_alerts_present(client, auth_headers):
    alerts = client.get("/alerts", headers=auth_headers).json()["items"]
    assert any(a["severity"] in ("High", "Medium") for a in alerts)
