"""Constraint and preference models."""

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Constraint(BaseModel):
    """A constraint, preference, rule, or correction."""

    id: Optional[UUID] = None
    conversation_id: UUID
    constraint_type: str = Field(
        ..., description="Type: preference, rule, correction, fact, ban"
    )
    constraint_key: str = Field(
        ..., description="Key identifier (e.g., 'answer_style', 'age', 'metrics_definition')"
    )
    constraint_value: Dict[str, Any] = Field(..., description="Constraint value as JSON")
    turn_number: int = Field(..., description="Turn when constraint was established")
    superseded_by: Optional[UUID] = Field(
        default=None, description="ID of constraint that supersedes this one"
    )
    is_active: bool = Field(default=True, description="Whether constraint is currently active")
    created_at: Optional[str] = None

