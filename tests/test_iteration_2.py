import pytest
from banana.assembler import ContextAssembler
from banana.config import Settings
from banana.db import FalkorDBClient
from banana.max_flow import MaxFlowScheduler
from banana.sandbox import SandboxManager
from banana.seeder import GraphSeeder
from banana.visualizer import GraphVisualizer


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_max_flow_scheduler(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    demand_items, demand_deps = assembler.fetch_demand_candidates("task_pricing_strategy")
    knowledge_items, knowledge_deps = assembler.fetch_knowledge_candidates()
    all_items = {it.canonical_id: it for it in demand_items + knowledge_items}
    all_deps = {**demand_deps}
    for k, v in knowledge_deps.items():
        if k in all_deps:
            all_deps[k].extend(v)
        else:
            all_deps[k] = list(v)

    scheduler = MaxFlowScheduler()
    res = scheduler.schedule(all_items, all_deps, token_budget=1600)

    assert res.token_budget == 1600
    assert res.total_flow > 0
    assert res.augmenting_paths_count > 0
    assert res.mandatory_policies_preserved is True
    assert res.dependency_preservation_pct >= 90.0
    assert res.scheduler_latency_ms > 0
    assert len(res.selected_canonical_ids) > 0


def test_ephemeral_sandbox(seeded_db: FalkorDBClient) -> None:
    sandbox = SandboxManager(session_id="test_sess_01", db_client=seeded_db)
    graph_name = sandbox.initialize_sandbox()
    assert "banana_scratch_" in graph_name

    # Run scenario simulation inside sandbox
    sim = sandbox.simulate_pricing_scenario(cloudscale_discount_pct=0.20, cogs_inflation_pct=0.05)
    assert sim["scenario"]["policy_compliant"] is True
    assert float(sim["scenario"]["projected_gross_margin"].replace("%", "")) >= 25.0
    assert "ApexCloud" in sim["sandbox_finding"]

    # Discard sandbox and verify it no longer exists
    sandbox.discard_sandbox()


def test_graph_visualizer_html(seeded_db: FalkorDBClient) -> None:
    visualizer = GraphVisualizer(seeded_db)
    html = visualizer.generate_html(selected_canonical_ids={"task_pricing_strategy", "policy_minimum_margin"})

    assert "<!DOCTYPE html>" in html
    assert "d3.v7.min.js" in html
    assert "Banana Dual Graph Visualizer" in html
    assert "task_pricing_strategy" in html
    assert "policy_minimum_margin" in html


def test_falkordb_cloud_config() -> None:
    cloud_settings = Settings(
        falkordb_url="falkor://demo_user:secret@my-cluster.falkordb.cloud:6379",
        falkordb_ssl=True,
    )
    assert cloud_settings.falkordb_url == "falkor://demo_user:secret@my-cluster.falkordb.cloud:6379"
    assert cloud_settings.falkordb_ssl is True
