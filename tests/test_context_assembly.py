import pytest
from banana.assembler import ContextAssembler, BudgetExceededError
from banana.db import FalkorDBClient
from banana.models import PriorityClass
from banana.seeder import GraphSeeder


@pytest.fixture(scope="module")
def seeded_db() -> FalkorDBClient:
    db = FalkorDBClient()
    seeder = GraphSeeder(db)
    seeder.seed_all(drop_existing=True)
    return db


def test_assembly_under_ample_budget(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    result = assembler.assemble(token_budget=4000)

    assert result.total_tokens <= 4000
    assert len(result.selected_items) > 0
    assert result.latency_ms > 0
    assert "BANANA GRAPH-ASSEMBLED CONTEXT" in result.formatted_prompt

    # Verify inclusion reasons recorded for every selected item
    for item in result.selected_items:
        assert item.canonical_id in result.inclusion_reasons


def test_progressive_load_shedding_under_tight_budget(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    tight_result = assembler.assemble(token_budget=1600, reserved_output_tokens=500)

    assert tight_result.total_tokens <= 1600
    assert len(tight_result.excluded_items) > 0

    # Ensure all Mandatory (P0) items remain selected
    selected_ids = {it.canonical_id for it in tight_result.selected_items}
    for it in tight_result.selected_items:
        if it.priority == PriorityClass.MANDATORY:
            assert it.canonical_id in selected_ids

    # Ensure background (P4) items are shed first
    excluded_priorities = [it.priority for it in tight_result.excluded_items]
    assert PriorityClass.BACKGROUND in excluded_priorities


def test_mandatory_policies_never_shed(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    result = assembler.assemble(token_budget=1800, reserved_output_tokens=600)

    selected_ids = {it.canonical_id for it in result.selected_items}
    mandatory_must_have = [
        "policy_minimum_margin",
        "policy_source_attribution",
        "policy_anti_predatory",
    ]
    for p in mandatory_must_have:
        assert p in selected_ids, f"Mandatory policy {p} was shed!"


def test_dependency_preservation(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    result = assembler.assemble(token_budget=2500)

    selected_ids = {it.canonical_id for it in result.selected_items}
    for child, prereq in result.preserved_dependencies:
        if child in selected_ids:
            assert prereq in selected_ids, f"Dependency violated: {child} kept without {prereq}"


def test_budget_exceeded_error_raised(seeded_db: FalkorDBClient) -> None:
    assembler = ContextAssembler(seeded_db)
    # Budget too small to hold even mandatory P0 instructions
    with pytest.raises(BudgetExceededError):
        assembler.assemble(token_budget=300, reserved_output_tokens=250)
