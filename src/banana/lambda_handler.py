"""AWS Lambda Handler for Banana Graph & Context Brain.

Provides serverless execution for:
- FalkorDB connection health checks
- Graph-aware context assembly with Edmonds-Karp load shedding
- Deterministic policy & architecture guardrails
- Cross-session persistent decision memory
- Cypher queries against FalkorDB Cloud

Zero idle infrastructure cost. Scales to zero.
"""

import json
import os
import time
from typing import Any, Dict, Optional

from banana.assembler import ContextAssembler
from banana.db import FalkorDBClient, get_db_client
from banana.guardrails import GuardrailsEngine
from banana.max_flow import MaxFlowScheduler
from banana.tools import AgentTools


def handler(event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """Main AWS Lambda entrypoint supporting both API Gateway / Function URL and direct invocation."""
    start_time = time.perf_counter()

    # Parse input from API Gateway HTTP body or direct event payload
    raw_body = event.get("body")
    if raw_body:
        if isinstance(raw_body, str):
            try:
                payload = json.loads(raw_body)
            except Exception:
                payload = {}
        else:
            payload = raw_body
    else:
        payload = event

    # Check if incoming request is a browser GET request asking for HTML landing page
    headers = event.get("headers", {}) if isinstance(event, dict) else {}
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    ).upper()
    accept_header = headers.get("accept", "").lower()

    # Serve interactive landing page for browser GET requests
    is_browser_request = http_method == "GET" and ("text/html" in accept_header or not accept_header or "*/*" in accept_header)
    query_params = event.get("queryStringParameters") or {}
    explicit_landing = query_params.get("view") == "landing" or event.get("action") == "landing"
    explicit_json = query_params.get("format") == "json" or "application/json" in accept_header

    if (is_browser_request and not explicit_json) or explicit_landing:
        from banana.landing_page import get_landing_page_html
        host = headers.get("host", "")
        lambda_url = f"https://{host}/" if host else ""
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            },
            "body": get_landing_page_html(lambda_url=lambda_url),
        }

    action = payload.get("action", "health").strip().lower()
    params = payload.get("params", payload)

    # Initialize FalkorDB connection (local or FalkorDB Cloud via FALKORDB_URL / env)
    db_client = get_db_client()

    response_data: Dict[str, Any] = {}
    status_code = 200

    try:
        # 1. Health Check
        if action in ["health", "ping", "doctor"]:
            health = db_client.check_connection()
            response_data = {
                "action": "health",
                "falkordb_status": health["status"],
                "target_host": health["host"],
                "latency_ms": health["latency_ms"],
                "read_write_verified": health["read_write_verified"],
                "error": health.get("error"),
            }
            if health["status"] != "ok":
                status_code = 503

        # 2. Context Orchestration / Knapsack
        elif action in ["orchestrate", "assemble_context"]:
            prompt = params.get("prompt", "")
            token_budget = int(params.get("token_budget", 1600))
            task_id = params.get("task_id", "task_pricing_strategy")

            assembler = ContextAssembler(db_client)
            demand_items, demand_deps = assembler.fetch_demand_candidates(task_id)
            knowledge_items, knowledge_deps = assembler.fetch_knowledge_candidates()

            all_items = {it.canonical_id: it for it in demand_items + knowledge_items}
            all_deps = {**demand_deps}
            for k, v in knowledge_deps.items():
                if k in all_deps:
                    all_deps[k].extend(v)
                else:
                    all_deps[k] = list(v)

            scheduler = MaxFlowScheduler()
            flow_res = scheduler.schedule(
                all_items=all_items,
                dependencies=all_deps,
                token_budget=token_budget,
                reserved_output_tokens=max(200, token_budget // 5),
            )

            selected_items = [all_items[cid] for cid in flow_res.selected_canonical_ids if cid in all_items]
            context_text = "\n\n".join([f"[{it.entity_type.value.upper()}] {it.canonical_id} ({it.title}):\n{it.content}" for it in selected_items])

            response_data = {
                "action": "orchestrate",
                "prompt": prompt,
                "token_budget": token_budget,
                "tokens_used": flow_res.total_tokens_used,
                "total_flow_utility": flow_res.total_flow,
                "mandatory_policies_preserved": flow_res.mandatory_policies_preserved,
                "dependency_preservation_pct": flow_res.dependency_preservation_pct,
                "selected_canonical_ids": flow_res.selected_canonical_ids,
                "shed_canonical_ids": flow_res.shedded_canonical_ids,
                "assembled_context": context_text,
            }

        # 3. Policy & Architecture Guardrails Check
        elif action in ["guardrails", "check_guardrails"]:
            engine = GuardrailsEngine(db_client=db_client)
            if "price" in params:
                price = float(params["price"])
                cogs = float(params.get("cogs", 600.0))
                margin_floor = float(params.get("margin_floor_pct", 0.25))
                res = engine.check_pricing_proposal(price, cogs, margin_floor)
            else:
                src_file = params.get("source_file", "")
                imp_mod = params.get("imported_module", "")
                res = engine.check_code_architecture(src_file, imp_mod)

            response_data = {
                "action": "guardrails",
                "compliant": res.compliant,
                "violations": [v.model_dump() for v in res.violations],
                "verified_rules_count": res.verified_rules_count,
            }

        # 4. Save Architectural Decision to Persistent Memory
        elif action in ["save_decision", "record_decision"]:
            tools = AgentTools(db_client)
            title = params.get("title", "Architectural Decision")
            finding = params.get("finding", "")
            supersedes = params.get("supersedes_id") or params.get("supersedes")
            res = tools.save_finding(title=title, finding=finding, supersedes_id=supersedes)
            response_data = {
                "action": "save_decision",
                "memory": res,
            }

        # 5. Query Persistent Decisions
        elif action in ["query_decisions", "list_decisions"]:
            tools = AgentTools(db_client)
            keyword = params.get("keyword", "")
            limit = int(params.get("limit", 20))
            findings = tools.list_findings(limit=limit)
            if keyword:
                kw = keyword.lower()
                findings = [f for f in findings if kw in f.get("title", "").lower() or kw in f.get("finding", "").lower()]
            response_data = {
                "action": "query_decisions",
                "count": len(findings),
                "decisions": findings,
            }

        # 6. Direct Cypher / Keyword Query in FalkorDB
        elif action in ["query", "query_graph"]:
            kg = db_client.get_knowledge_graph()
            cypher_or_kw = params.get("query", "").strip()
            if cypher_or_kw.upper().startswith("MATCH") or cypher_or_kw.upper().startswith("RETURN"):
                res = kg.query(cypher_or_kw)
                response_data = {"action": "query", "result": res.result_set}
            else:
                cypher = """
                MATCH (n)
                WHERE (n.canonical_id IS NOT NULL AND n.canonical_id CONTAINS $kw)
                   OR (n.title IS NOT NULL AND n.title CONTAINS $kw)
                   OR (n.content IS NOT NULL AND n.content CONTAINS $kw)
                RETURN labels(n) AS labels, properties(n) AS props
                LIMIT 15
                """
                res = kg.query(cypher, {"kw": cypher_or_kw})
                records = [{"labels": r[0], "properties": r[1]} for r in res.result_set]
                response_data = {"action": "query", "keyword": cypher_or_kw, "matches": records}

        else:
            status_code = 400
            response_data = {
                "error": f"Unknown action: '{action}'",
                "supported_actions": [
                    "health",
                    "orchestrate",
                    "guardrails",
                    "save_decision",
                    "query_decisions",
                    "query",
                ],
            }

    except Exception as exc:
        status_code = 500
        response_data = {
            "error": str(exc),
            "action": action,
        }

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response_data["latency_ms"] = total_latency_ms

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        },
        "body": json.dumps(response_data),
    }
