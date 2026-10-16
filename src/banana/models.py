from enum import Enum, IntEnum
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from banana.tokenizer import count_tokens


class PriorityClass(IntEnum):
    """Explicit priority classes for graph-aware context assembly and load shedding."""
    MANDATORY = 0      # Non-negotiable security policies, system constraints
    TOOL_SCHEMA = 1    # Required tool definitions and direct execution schemas
    EVIDENCE = 2       # High-value factual groundings, pricing metrics, quotations
    MEMORY = 3         # Persistent cross-session decisions and findings
    BACKGROUND = 4     # Peripheral context, company overviews, general market context


class EntityType(str, Enum):
    """Core entity types across Demand and Knowledge graphs."""
    TASK = "Task"
    REQUIREMENT = "Requirement"
    POLICY = "Policy"
    TOOL = "Tool"
    COMPANY = "Company"
    PRODUCT = "Product"
    COMPETITOR = "Competitor"
    DOCUMENT = "Document"
    EVIDENCE = "Evidence"
    MEMORY = "Memory"


def calculate_partition_salt(canonical_id: str, num_buckets: int = 3) -> str:
    """Compute deterministic storage partition salt ('+1', '+2', '+3') from canonical ID."""
    digest = int(hashlib.sha256(canonical_id.encode("utf-8")).hexdigest(), 16)
    bucket = (digest % num_buckets) + 1
    return f"+{bucket}"


class ContextItem(BaseModel):
    """Canonical representation of any context candidate in Banana."""
    canonical_id: str = Field(description="Stable unique canonical identifier")
    entity_type: EntityType = Field(description="Logical entity type")
    title: str = Field(description="Human-readable title or label")
    content: str = Field(description="Textual representation of content")
    provenance: Optional[str] = Field(default=None, description="Source provenance or citation")
    priority: PriorityClass = Field(default=PriorityClass.EVIDENCE, description="Context priority tier")
    token_cost: int = Field(default=0, description="Estimated token cost")
    partition_salt: Optional[str] = Field(default=None, description="Partition salt bucket for storage (+1, +2, +3)")
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite canonical IDs")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary typed metadata")

    def model_post_init(self, __context: Any) -> None:
        """Automatically compute token cost and partition salt if not explicitly set."""
        if self.partition_salt is None:
            self.partition_salt = calculate_partition_salt(self.canonical_id)
        if self.token_cost == 0 and self.content:
            # Tokenize title + content + provenance
            full_text = f"{self.title}\n{self.content}"
            if self.provenance:
                full_text += f"\nSource: {self.provenance}"
            self.token_cost = count_tokens(full_text)


class GraphRelationship(BaseModel):
    """Directed relationship between two canonical entities."""
    source_id: str
    target_id: str
    rel_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
