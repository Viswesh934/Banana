"""Tests for Banana's AWS Lambda Serverless Handler."""

import json
from banana.lambda_handler import handler


def test_lambda_health_action() -> None:
    """Test Lambda health check action against FalkorDB."""
    event = {"action": "health"}
    resp = handler(event)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["action"] == "health"
    assert body["falkordb_status"] == "ok"
    assert body["read_write_verified"] is True


def test_lambda_api_gateway_event_wrapper() -> None:
    """Test Lambda invocation when wrapped in API Gateway / Lambda Function URL format."""
    event = {
        "rawPath": "/v1/guardrails",
        "headers": {"content-type": "application/json"},
        "body": json.dumps({
            "action": "guardrails",
            "params": {"price": 700.0, "cogs": 600.0},
        }),
    }
    resp = handler(event)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["action"] == "guardrails"
    assert body["compliant"] is False
    assert len(body["violations"]) > 0


def test_lambda_orchestrate_and_decision() -> None:
    """Test Lambda context orchestration and decision logging."""
    # 1. Orchestrate
    orch_event = {
        "action": "orchestrate",
        "params": {"prompt": "Analyze pricing under $750 floor", "token_budget": 1600},
    }
    resp_orch = handler(orch_event)
    assert resp_orch["statusCode"] == 200
    body_orch = json.loads(resp_orch["body"])
    assert body_orch["mandatory_policies_preserved"] is True
    assert body_orch["tokens_used"] <= 1600

    # 2. Save Decision
    dec_event = {
        "action": "save_decision",
        "params": {
            "title": "Lambda Deployment Decision",
            "finding": "Deploy Banana graph brain to AWS Lambda backed by FalkorDB Cloud",
        },
    }
    resp_dec = handler(dec_event)
    assert resp_dec["statusCode"] == 200
    body_dec = json.loads(resp_dec["body"])
    assert body_dec["memory"]["status"] == "success"

    # 3. Query Decisions
    query_event = {
        "action": "query_decisions",
        "params": {"keyword": "Lambda"},
    }
    resp_query = handler(query_event)
    assert resp_query["statusCode"] == 200
    body_query = json.loads(resp_query["body"])
    assert body_query["count"] >= 1
