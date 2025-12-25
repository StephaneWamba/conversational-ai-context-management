"""Constraint manager for extracting and managing user constraints, preferences, and corrections."""

import json
import re
from typing import Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.models.constraints import Constraint
from app.services.database import DatabaseService


class ConstraintManager:
    """Manages user constraints, preferences, and corrections."""

    def __init__(self, database: DatabaseService) -> None:
        """Initialize constraint manager."""
        self.database = database

    async def extract_constraints(
        self, conversation_id: UUID, messages: List[Dict[str, str]], turn_number: int
    ) -> List[Constraint]:
        """
        Extract constraints, preferences, and corrections from recent messages.

        Args:
            conversation_id: Conversation ID
            messages: Recent messages to analyze
            turn_number: Current turn number

        Returns:
            List of extracted constraints
        """
        constraints = []
        recent_text = " ".join([msg.get("content", "")
                               for msg in messages[-5:]])

        correction_patterns = [
            r"(?:actually|correct|not|wrong).*?(\d+).*?(?:not|but|actually).*?(\d+)",
            r"(\d+).*?(?:not|but|actually).*?(\d+)",
        ]

        for pattern in correction_patterns:
            matches = re.finditer(pattern, recent_text, re.IGNORECASE)
            for match in matches:
                old_val, new_val = match.groups()
                if old_val != new_val:
                    existing = [c for c in constraints if c.constraint_type == "correction"
                                and c.constraint_value.get("old_value") == old_val
                                and c.constraint_value.get("new_value") == new_val]
                    if not existing:
                        constraints.append(
                            Constraint(
                                conversation_id=conversation_id,
                                constraint_type="correction",
                                constraint_key="numeric_fact",
                                constraint_value={
                                    "old_value": old_val, "new_value": new_val},
                                turn_number=turn_number,
                            )
                        )

        # Extract preferences
        if re.search(r"prefer.*?(?:short|brief|concise|structured|bullet)", recent_text, re.IGNORECASE):
            existing = [
                c for c in constraints if c.constraint_key == "answer_style"]
            if not existing:
                constraints.append(
                    Constraint(
                        conversation_id=conversation_id,
                        constraint_type="preference",
                        constraint_key="answer_style",
                        constraint_value={"style": "short_bullet_points"},
                        turn_number=turn_number,
                    )
                )

        if re.search(r"don't.*?like.*?(?:technical|verbose)", recent_text, re.IGNORECASE):
            existing = [
                c for c in constraints if c.constraint_key == "technical_depth"]
            if not existing:
                constraints.append(
                    Constraint(
                        conversation_id=conversation_id,
                        constraint_type="preference",
                        constraint_key="technical_depth",
                        constraint_value={"depth": "minimal_unless_asked"},
                        turn_number=turn_number,
                    )
                )

        # Extract rules (metrics definition, dashboard meaning, etc.)
        metrics_match = re.search(
            r"when.*?say.*?\"?metrics\"?.*?mean.*?([A-Z]+(?:\s*,\s*[A-Z]+)*)", recent_text, re.IGNORECASE
        )
        if metrics_match:
            metrics_str = metrics_match.group(1)
            metrics = [m.strip() for m in metrics_str.split(",")]
            existing = [
                c for c in constraints if c.constraint_key == "metrics_definition"]
            if not existing:
                constraints.append(
                    Constraint(
                        conversation_id=conversation_id,
                        constraint_type="rule",
                        constraint_key="metrics_definition",
                        constraint_value={"allowed_metrics": metrics},
                        turn_number=turn_number,
                    )
                )

        # Extract dashboard definition
        dashboard_match = re.search(
            r"(?:when|if).*?say.*?\"?dashboard\"?.*?(?:mean|refer).*?(web|mobile)", recent_text, re.IGNORECASE
        )
        if dashboard_match:
            dashboard_type = dashboard_match.group(1).lower()
            existing = [c for c in constraints if c.constraint_key ==
                        "dashboard_definition"]
            if not existing:
                constraints.append(
                    Constraint(
                        conversation_id=conversation_id,
                        constraint_type="rule",
                        constraint_key="dashboard_definition",
                        constraint_value={"type": dashboard_type},
                        turn_number=turn_number,
                    )
                )

        # Extract bans (MongoDB, etc.)
        ban_match = re.search(
            r"(?:don't|do not|never).*?(?:suggest|use|mention).*?([A-Z][a-zA-Z]+)", recent_text, re.IGNORECASE
        )
        if ban_match:
            banned_item = ban_match.group(1)
            existing = [c for c in constraints if c.constraint_key == "tech_ban"
                        and c.constraint_value.get("banned_item") == banned_item]
            if not existing:
                constraints.append(
                    Constraint(
                        conversation_id=conversation_id,
                        constraint_type="ban",
                        constraint_key="tech_ban",
                        constraint_value={"banned_item": banned_item},
                        turn_number=turn_number,
                    )
                )

        return constraints

    async def store_constraint(self, constraint: Constraint) -> Constraint:
        """Store a constraint in the database."""
        if not self.database.pool:
            raise DatabaseError("Database not connected")

        async with self.database.pool.acquire() as conn:
            if constraint.constraint_type == "correction":
                await conn.execute(
                    """
                    UPDATE conversation_constraints
                    SET is_active = FALSE, superseded_by = $1
                    WHERE conversation_id = $2
                      AND constraint_key = $3
                      AND is_active = TRUE
                    """,
                    constraint.id,
                    constraint.conversation_id,
                    constraint.constraint_key,
                )

            row = await conn.fetchrow(
                """
                INSERT INTO conversation_constraints
                (conversation_id, constraint_type, constraint_key, constraint_value, turn_number, is_active)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                RETURNING id, conversation_id, constraint_type, constraint_key, constraint_value,
                          turn_number, superseded_by, is_active, created_at
                """,
                constraint.conversation_id,
                constraint.constraint_type,
                constraint.constraint_key,
                constraint.constraint_value,
                constraint.turn_number,
                constraint.is_active,
            )

            constraint_value = row["constraint_value"]
            if isinstance(constraint_value, str):
                constraint_value = json.loads(constraint_value)
            if not isinstance(constraint_value, dict):
                constraint_value = {"value": constraint_value}

            return Constraint(
                id=row["id"],
                conversation_id=row["conversation_id"],
                constraint_type=row["constraint_type"],
                constraint_key=row["constraint_key"],
                constraint_value=constraint_value,
                turn_number=row["turn_number"],
                superseded_by=row["superseded_by"],
                is_active=row["is_active"],
                created_at=row["created_at"].isoformat(
                ) if row["created_at"] else None,
            )

    async def get_active_constraints(self, conversation_id: UUID) -> List[Constraint]:
        """Get all active constraints for a conversation."""
        if not self.database.pool:
            raise DatabaseError("Database not connected")

        async with self.database.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_id, constraint_type, constraint_key, constraint_value,
                       turn_number, superseded_by, is_active, created_at
                FROM conversation_constraints
                WHERE conversation_id = $1 AND is_active = TRUE
                ORDER BY turn_number ASC
                """,
                conversation_id,
            )

            constraints = []
            for row in rows:
                constraint_value = row["constraint_value"]
                if isinstance(constraint_value, str):
                    try:
                        constraint_value = json.loads(constraint_value)
                    except (json.JSONDecodeError, TypeError):
                        constraint_value = {"raw": constraint_value}
                if not isinstance(constraint_value, dict):
                    constraint_value = {"value": constraint_value}

                constraints.append(
                    Constraint(
                        id=row["id"],
                        conversation_id=row["conversation_id"],
                        constraint_type=row["constraint_type"],
                        constraint_key=row["constraint_key"],
                        constraint_value=constraint_value,
                        turn_number=row["turn_number"],
                        superseded_by=row["superseded_by"],
                        is_active=row["is_active"],
                        created_at=row["created_at"].isoformat(
                        ) if row["created_at"] else None,
                    )
                )
            return constraints

    def build_constraint_prompt(self, constraints: List[Constraint]) -> str:
        """
        Build a constraint prompt for the system message.

        Args:
            constraints: List of active constraints

        Returns:
            Formatted constraint prompt
        """
        if not constraints:
            return ""

        prompt_parts = ["\n\nCONSTRAINTS AND PREFERENCES (strictly follow):"]

        # Group by type
        preferences = [
            c for c in constraints if c.constraint_type == "preference"]
        rules = [c for c in constraints if c.constraint_type == "rule"]
        corrections = [
            c for c in constraints if c.constraint_type == "correction"]
        bans = [c for c in constraints if c.constraint_type == "ban"]

        if preferences:
            prompt_parts.append("\nPREFERENCES:")
            for pref in preferences:
                if pref.constraint_key == "answer_style":
                    prompt_parts.append(
                        "- Answer style: Short, structured, bullet points")
                elif pref.constraint_key == "technical_depth":
                    prompt_parts.append(
                        "- Technical depth: Minimal unless explicitly asked")

        if rules:
            prompt_parts.append("\nRULES:")
            for rule in rules:
                if rule.constraint_key == "metrics_definition":
                    metrics = rule.constraint_value.get("allowed_metrics", [])
                    prompt_parts.append(
                        f"- When user says 'metrics', ONLY refer to: {', '.join(metrics)}"
                    )
                elif rule.constraint_key == "dashboard_definition":
                    dashboard_type = rule.constraint_value.get("type", "web")
                    prompt_parts.append(
                        f"- When user says 'dashboard', it always means {dashboard_type} dashboard, not mobile"
                    )

        if corrections:
            prompt_parts.append("\nCORRECTIONS (use these values):")
            for corr in corrections:
                old_val = corr.constraint_value.get("old_value")
                new_val = corr.constraint_value.get("new_value")
                if old_val and new_val:
                    prompt_parts.append(
                        f"- Use {new_val} (corrected from {old_val})")

        if bans:
            prompt_parts.append("\nBANS (do not suggest):")
            for ban in bans:
                item = ban.constraint_value.get("banned_item")
                if item:
                    prompt_parts.append(f"- Do NOT suggest or mention: {item}")

        prompt_parts.append(
            "\nCRITICAL: Do not violate any constraints above.")

        return "\n".join(prompt_parts)
