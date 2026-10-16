import pytest
from typer.testing import CliRunner
from banana.cli import app
from banana.db import FalkorDBClient
from banana.seeder import GraphSeeder

runner = CliRunner()


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_demo_command_execution(seeded_db: FalkorDBClient) -> None:
    result = runner.invoke(app, ["demo", "--budget", "1600"])
    assert result.exit_code == 0
    assert "BANANA — GRAPH-AWARE CONTEXT ORCHESTRATION AGENT" in result.stdout
    assert "Incoming Business Directive" in result.stdout
    assert "Demand Graph Extraction" in result.stdout
    assert "Knowledge Graph Candidate Match" in result.stdout
    assert "Progressive Load Shedding" in result.stdout
    assert "Grounded Recommendation" in result.stdout
    assert "Persistent Memory Committed" in result.stdout
    assert "Scientific Benchmark Comparison" in result.stdout
