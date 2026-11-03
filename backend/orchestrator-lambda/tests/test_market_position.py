import json

import pytest

from src.config.prompts import MARKET_POSITION_PROMPT
from src.handlers import orchestrator


MARKET_ANALYSIS = {"meta": {"sector": "agriculture", "period": "2024-2025"}, "tables": []}


@pytest.fixture
def run(monkeypatch):
    calls = []

    def generate_only(context, system_prompt):
        calls.append((context, system_prompt))
        return {"output": {"text": json.dumps({"client_name": "model name", "analysis_id": "x"})}}

    monkeypatch.setattr(orchestrator.llm_service, "generate_only", generate_only)
    monkeypatch.setattr(orchestrator.storage, "read_file", lambda bucket, key: json.dumps(MARKET_ANALYSIS))
    monkeypatch.setattr(orchestrator.storage, "save_json", lambda result, file_id, prefix: None)

    def invoke(**fields):
        event = {
            "analysis_type": "market_position",
            "market_analysis_key": "market_analysis/a.json",
            "client_name": "Žito d.o.o.",
            "analysis_id": "abc",
            "total_revenue": 165901000,
            "commodities": [{"name": "wheat", "revenue_pct": 60}, {"name": "corn", "revenue_pct": 40}],
            "primary_currency": "RSD",
            "fx_rate_eur_rsd": 117.2,
            "fx_rate_date": "2025-12-31",
            **fields,
        }
        response = orchestrator.lambda_handler(event, None)
        return response, calls

    return invoke


def test_context_has_only_analyst_inputs_and_market_analysis(run):
    response, calls = run()

    assert response["statusCode"] == 200
    context, system_prompt = calls[0]
    assert system_prompt == MARKET_POSITION_PROMPT
    assert context.startswith("=== PARAMETERS ===\ntotal_revenue: 165901000\nprimary_currency: RSD\n")
    assert "  - wheat: 60% of revenue\n  - corn: 40% of revenue" in context
    assert "fx_rate_eur_rsd: 117.2\nfx_rate_date: 2025-12-31" in context
    assert json.dumps(MARKET_ANALYSIS) in context
    assert "CLIENT_KEY_FINANCIALS" not in context and "CLIENT_KEY_FINANCIALS" not in system_prompt

    body = json.loads(response["body"])
    assert body["analysis_id"] == "market_position/abc.json"
    assert body["client_name"] == "Žito d.o.o."


def test_missing_fx_rate_is_null(run):
    _, calls = run(fx_rate_eur_rsd=None, fx_rate_date=None)

    assert "fx_rate_eur_rsd: null\nfx_rate_date: null" in calls[0][0]


@pytest.mark.parametrize("fields, message", [
    ({"total_revenue": None}, "total_revenue"),
    ({"total_revenue": 0}, "total_revenue"),
    ({"total_revenue": "100"}, "total_revenue"),
    ({"commodities": []}, "commodities"),
    ({"commodities": [{"name": "wheat", "revenue_pct": 0}]}, "revenue_pct"),
    ({"commodities": [{"name": "wheat", "revenue_pct": 70}, {"name": "corn", "revenue_pct": 40}]}, "at most 100"),
])
def test_invalid_inputs_are_rejected(run, fields, message):
    response, calls = run(**fields)

    assert response["statusCode"] == 400
    assert message in response["body"]
    assert calls == []
