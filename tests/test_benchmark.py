import pytest
from banana.benchmark import BenchmarkSuite
from banana.db import FalkorDBClient
from banana.seeder import GraphSeeder


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_benchmark_metrics_computation(seeded_db: FalkorDBClient) -> None:
    suite = BenchmarkSuite(seeded_db)
    metrics = suite.run_all(budgets=[1100, 1600])

    assert len(metrics) == 6  # 3 strategies * 2 budgets
    strategies = {m.strategy for m in metrics}
    assert "Baseline A (Naive Truncation)" in strategies
    assert "Baseline B (Relevance Top-K)" in strategies
    assert "Banana (Graph-Aware Knapsack)" in strategies

    # Check Banana metrics at budget 1100
    banana_1100 = next(m for m in metrics if "Banana" in m.strategy and m.budget == 1100)
    assert banana_1100.policy_preservation_pct == 100.0
    assert banana_1100.dependency_preservation_pct == 100.0
    assert banana_1100.budget_violation is False

    # Check that Baseline A suffers from policy loss due to truncation
    baseline_a_1100 = next(m for m in metrics if "Baseline A" in m.strategy and m.budget == 1100)
    assert baseline_a_1100.policy_preservation_pct < 100.0

    # Check that Baseline B suffers from broken dependencies
    baseline_b_1100 = next(m for m in metrics if "Baseline B" in m.strategy and m.budget == 1100)
    assert baseline_b_1100.dependency_preservation_pct < 100.0
