import pytest
from typer.testing import CliRunner
from banana.cli import app
from banana.config import Settings
from banana.db import FalkorDBClient
from banana.tokenizer import count_tokens, get_token_counter

runner = CliRunner()


def test_settings_defaults_and_validation() -> None:
    settings = Settings(_env_file=None)
    assert settings.falkordb_host == "localhost"
    assert settings.falkordb_port == 6379
    assert settings.demand_graph_name == "banana_demand"
    assert settings.knowledge_graph_name == "banana_knowledge"
    assert settings.default_token_budget == 4000

    # Invalid port validation
    with pytest.raises(ValueError):
        Settings(falkordb_port=99999)

    with pytest.raises(ValueError):
        Settings(falkordb_port=0)


def test_tokenizer() -> None:
    counter = get_token_counter()
    assert counter.count("") == 0
    text = "Banana is a graph-aware context orchestration agent."
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_falkordb_connection_and_read_write() -> None:
    client = FalkorDBClient()
    health = client.check_connection()
    assert health["status"] == "ok"
    assert health["read_write_verified"] is True
    assert health["latency_ms"] > 0
    assert health["error"] is None


def test_falkordb_error_handling_graceful() -> None:
    # Test connection to unreachable port
    bad_settings = Settings(falkordb_port=59999)
    client = FalkorDBClient(settings=bad_settings)
    health = client.check_connection()
    assert health["status"] == "error"
    assert health["read_write_verified"] is False
    assert "docker compose up -d" in health["error"] or "Connection" in health["error"]


def test_cli_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Banana Diagnostic & Environment Doctor" in result.stdout
    assert "FalkorDB Database" in result.stdout
    assert "All core systems operational" in result.stdout
