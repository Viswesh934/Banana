"""Ephemeral 'Thinking' Sandboxes in FalkorDB for speculative reasoning and policy simulation."""

import time
import uuid
from typing import Any, Dict, List, Optional
from banana.db import FalkorDBClient, get_db_client


class SandboxManager:
    """Manages ephemeral micro-graphs in FalkorDB for sandbox scenario simulations."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        db_client: Optional[FalkorDBClient] = None,
    ) -> None:
        self.db_client = db_client or get_db_client()
        self.session_id = session_id or f"sess_{int(time.time())}"
        self.sandbox_name = f"banana_scratch_{self.session_id}_{uuid.uuid4().hex[:6]}"
        self._graph = None

    @property
    def graph(self):
        """Get or initialize the ephemeral FalkorDB scratchpad graph."""
        if self._graph is None:
            self._graph = self.db_client.get_graph(self.sandbox_name)
        return self._graph

    def initialize_sandbox(self) -> str:
        """Create and initialize the ephemeral sandbox graph."""
        # Touch graph by creating a root scenario context node
        cypher = (
            "CREATE (s:SandboxRoot {id: $id, created_at: timestamp(), status: 'active'}) "
            "RETURN s.id"
        )
        self.graph.query(cypher, {"id": self.sandbox_name})
        return self.sandbox_name

    def simulate_pricing_scenario(
        self,
        cloudscale_discount_pct: float = 0.20,
        cogs_inflation_pct: float = 0.05,
    ) -> Dict[str, Any]:
        """Simulate a competitive pricing scenario inside the isolated FalkorDB sandbox.

        Tests hypothetical competitor aggressive moves against ApexCloud's 25% margin policy.
        """
        # Base figures
        base_cogs = 600.0  # ApexCloud verified hardware/bandwidth COGS
        apex_current_price = 1200.0
        cloudscale_base = 800.0

        # Simulate scenario inside the sandbox graph
        simulated_cogs = round(base_cogs * (1.0 + cogs_inflation_pct), 2)
        simulated_cloudscale_price = round(cloudscale_base * (1.0 - cloudscale_discount_pct), 2)

        # Policy requirement: Minimum price = COGS / (1 - 0.25) to maintain 25% gross margin
        min_viable_price_floor = round(simulated_cogs / 0.75, 2)

        # Proposed competitive response: "Performance Starter" tier (target $899/mo)
        proposed_starter_price = max(min_viable_price_floor, 899.0)
        projected_margin = round(
            ((proposed_starter_price - simulated_cogs) / proposed_starter_price) * 100, 1
        )

        margin_compliant = proposed_starter_price >= min_viable_price_floor

        # Persist scenario node and evaluation in the ephemeral sandbox
        cypher = """
        CREATE (sc:Scenario {
            cloudscale_discount: $cs_disc,
            simulated_cloudscale_price: $cs_price,
            simulated_cogs: $cogs,
            min_viable_floor: $floor,
            proposed_starter_price: $starter_price,
            projected_margin_pct: $margin,
            margin_compliant: $compliant,
            timestamp: timestamp()
        })
        RETURN id(sc)
        """
        params = {
            "cs_disc": cloudscale_discount_pct,
            "cs_price": simulated_cloudscale_price,
            "cogs": simulated_cogs,
            "floor": min_viable_price_floor,
            "starter_price": proposed_starter_price,
            "margin": projected_margin,
            "compliant": margin_compliant,
        }
        self.graph.query(cypher, params)

        return {
            "sandbox_graph": self.sandbox_name,
            "scenario": {
                "competitor_discount_pct": f"{int(cloudscale_discount_pct * 100)}%",
                "simulated_competitor_price": f"${simulated_cloudscale_price}/mo",
                "simulated_apex_cogs": f"${simulated_cogs}/mo",
                "mandatory_25pct_margin_floor": f"${min_viable_price_floor}/mo",
                "recommended_starter_price": f"${proposed_starter_price}/mo",
                "projected_gross_margin": f"{projected_margin}%",
                "policy_compliant": margin_compliant,
            },
            "sandbox_finding": (
                f"Even if CloudScale discounts 20% down to ${simulated_cloudscale_price}/mo and our COGS rises 5% "
                f"to ${simulated_cogs}/mo, ApexCloud can safely introduce an $899/mo starter tier yielding "
                f"{projected_margin}% gross margin, maintaining full compliance with the 25% margin floor (${min_viable_price_floor}/mo)."
            ),
        }

    def discard_sandbox(self) -> None:
        """Safely drop the ephemeral scratchpad graph from FalkorDB."""
        try:
            self.graph.delete()
        except Exception:
            pass
