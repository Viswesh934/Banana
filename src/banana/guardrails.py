"""Deterministic Policy & Architecture Guardrails Engine for Banana.

Provides zero-token, sub-millisecond rule validation for coding agents:
- Business & financial policy enforcement (e.g. gross margin floor >= 25%)
- Architecture boundary rules (e.g. UI layer cannot directly import DB layer)
- Anti-pattern detection and custom repo rules (.banana/rules.json)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from banana.db import FalkorDBClient, get_db_client


class RuleViolation(BaseModel):
    rule_id: str
    severity: str = "ERROR"  # ERROR, WARNING
    description: str
    citation: Optional[str] = None
    suggested_fix: Optional[str] = None


class ValidationResult(BaseModel):
    compliant: bool
    violations: List[RuleViolation] = Field(default_factory=list)
    verified_rules_count: int = 0
    latency_ms: float = 0.0


class GuardrailsEngine:
    """Evaluates proposed actions against deterministic business & architectural rules."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None, repo_dir: Optional[str] = None) -> None:
        self.db_client = db_client or get_db_client()
        self.repo_dir = Path(repo_dir or Path.cwd()).resolve()

    def check_pricing_proposal(self, proposed_price: float, cogs: float = 600.0, margin_floor_pct: float = 0.25) -> ValidationResult:
        """Validate proposed pricing against minimum gross margin policy floor."""
        violations = []
        min_allowed_price = cogs / (1.0 - margin_floor_pct)
        actual_margin = (proposed_price - cogs) / proposed_price if proposed_price > 0 else 0.0

        if actual_margin < margin_floor_pct or proposed_price < min_allowed_price:
            violations.append(RuleViolation(
                rule_id="policy_minimum_margin",
                severity="ERROR",
                description=f"Proposed price ${proposed_price:.2f}/mo yields {actual_margin*100:.1f}% margin, which violates the mandatory {margin_floor_pct*100:.0f}% gross margin floor.",
                citation="policy_minimum_margin (Pricing Model Floor)",
                suggested_fix=f"Increase price to at least ${min_allowed_price:.2f}/mo (or offer $899 Starter Tier with non-core feature shedding).",
            ))

        return ValidationResult(
            compliant=len(violations) == 0,
            violations=violations,
            verified_rules_count=1,
        )

    def check_code_architecture(self, source_file: str, imported_module: str) -> ValidationResult:
        """Verify architectural layer boundaries (e.g. UI layer importing DB directly)."""
        violations = []
        src_lower = source_file.lower().replace("\\", "/")
        imp_lower = imported_module.lower()

        # Rule: Presentation / UI layer should never import DB directly
        if ("ui" in src_lower or "app.py" in src_lower or "views" in src_lower) and ("database" in imp_lower or "sql" in imp_lower):
            violations.append(RuleViolation(
                rule_id="arch_layer_violation_db_in_ui",
                severity="ERROR",
                description=f"Presentation layer '{source_file}' directly imports low-level database module '{imported_module}'.",
                citation="Architecture Guidelines: Clean Architecture Layer Isolation",
                suggested_fix="Route data requests through the Service or Repository layer instead of direct DB queries.",
            ))

        # Check custom rules file if exists (.banana/rules.json)
        custom_rules_file = self.repo_dir / ".banana" / "rules.json"
        if custom_rules_file.exists():
            try:
                rules_data = json.loads(custom_rules_file.read_text(encoding="utf-8"))
                for rule in rules_data.get("rules", []):
                    forbidden = rule.get("forbidden_import")
                    applies_to = rule.get("applies_to", "")
                    if forbidden and forbidden in imp_lower and applies_to in src_lower:
                        violations.append(RuleViolation(
                            rule_id=rule.get("id", "custom_rule"),
                            severity=rule.get("severity", "ERROR"),
                            description=rule.get("description", f"Import '{imported_module}' forbidden in '{source_file}'"),
                            citation=rule.get("citation", "Custom Repo Policy"),
                            suggested_fix=rule.get("suggested_fix"),
                        ))
            except Exception:
                pass

        return ValidationResult(
            compliant=len(violations) == 0,
            violations=violations,
            verified_rules_count=2,
        )

    def check_generic_action(self, action_name: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Check generic tool or action call against registered policy invariants."""
        if "price" in parameters:
            try:
                price = float(parameters["price"])
                cogs = float(parameters.get("cogs", 600.0))
                return self.check_pricing_proposal(price, cogs)
            except Exception:
                pass

        if "source_file" in parameters and "imported_module" in parameters:
            return self.check_code_architecture(parameters["source_file"], parameters["imported_module"])

        return ValidationResult(compliant=True, violations=[], verified_rules_count=1)
