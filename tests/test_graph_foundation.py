import pytest
from banana.db import FalkorDBClient
from banana.models import ContextItem, EntityType, PriorityClass, calculate_partition_salt
from banana.seeder import GraphSeeder, get_seed_demand_items, get_seed_knowledge_items
from banana.inspector import GraphInspector


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    """Fixture ensuring seeded dual graphs exist."""
    db_client = FalkorDBClient()
    seeder = GraphSeeder(db_client)
    seeder.seed_all(drop_existing=True)
    return db_client


def test_models_and_partitioning() -> None:
    item = ContextItem(
        canonical_id="test_item_123",
        entity_type=EntityType.EVIDENCE,
        title="Test Item",
        content="This is sample content for testing tokenization and partitioning.",
    )
    assert item.priority == PriorityClass.EVIDENCE
    assert item.token_cost > 0
    assert item.partition_salt in ["+1", "+2", "+3"]

    # Verify deterministic salt
    salt1 = calculate_partition_salt("test_item_123")
    salt2 = calculate_partition_salt("test_item_123")
    assert salt1 == salt2


def test_seed_idempotency(seeded_db: FalkorDBClient) -> None:
    seeder = GraphSeeder(seeded_db)

    # First seeding was in fixture, run second time without dropping
    res = seeder.seed_all(drop_existing=False)
    assert res["demand"]["nodes_created"] == 13
    assert res["knowledge"]["nodes_created"] == 17

    # Verify counts in database remain exactly 13 and 17
    inspector = GraphInspector(seeded_db)
    demand_stats = inspector.inspect_graph(seeded_db.settings.demand_graph_name)
    knowledge_stats = inspector.inspect_graph(seeded_db.settings.knowledge_graph_name)

    assert demand_stats["node_count"] == 13
    assert demand_stats["edge_count"] == 15
    assert knowledge_stats["node_count"] == 17
    assert knowledge_stats["edge_count"] == 13


def test_demand_graph_traversal(seeded_db: FalkorDBClient) -> None:
    graph = seeded_db.get_demand_graph()

    # Query policies governing the pricing strategy task
    query = """
    MATCH (t:Task {canonical_id: 'task_pricing_strategy'})-[:GOVERNED_BY]->(p:Policy)
    RETURN p.canonical_id, p.priority, p.title
    ORDER BY p.canonical_id
    """
    res = graph.query(query)
    assert len(res.result_set) == 3
    policy_ids = [row[0] for row in res.result_set]
    assert "policy_minimum_margin" in policy_ids
    assert "policy_source_attribution" in policy_ids
    assert "policy_anti_predatory" in policy_ids

    # Verify priority 0 for policies
    for row in res.result_set:
        assert row[1] == int(PriorityClass.MANDATORY)


def test_knowledge_graph_traversal(seeded_db: FalkorDBClient) -> None:
    graph = seeded_db.get_knowledge_graph()

    # Traverse from Competitor to Product to Evidence
    query = """
    MATCH (c:Competitor {canonical_id: 'comp_cloudscale'})<-[:OFFERED_BY]-(p:Product)<-[:EVALUATES]-(e:Evidence)
    RETURN c.canonical_id, p.canonical_id, e.canonical_id, e.title
    """
    res = graph.query(query)
    assert len(res.result_set) >= 1
    row = res.result_set[0]
    assert row[0] == "comp_cloudscale"
    assert row[1] == "prod_cloudscale_standard"
    assert row[2] == "ev_cloudscale_hidden_egress"
    assert "CloudScale" in row[3]
