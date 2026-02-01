"""Domain models for the Legacy Knowledge Extraction demo."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Legacy Knowledge Extraction layer
# ---------------------------------------------------------------------------

class DataField(BaseModel):
    field_name: str
    field_type: str
    scale: int | None = None


class BusinessRule(BaseModel):
    rule_id: str
    condition: str
    action: str
    description: str


class DecisionTraceAuthority(BaseModel):
    file: str
    rule: str
    lines: str


class LegacyKnowledge(BaseModel):
    business_rules: list[BusinessRule]
    canonical_data: list[DataField]
    decision_trace: DecisionTraceAuthority


# ---------------------------------------------------------------------------
# XAI Decision Plane
# ---------------------------------------------------------------------------

class CanonicalQuestion(BaseModel):
    user_cx_id: str
    question: str


class SlotSchema(BaseModel):
    time_period: str | None = None
    product: str | None = None
    merchant: str | None = None
    transaction_type: str | None = None


class GovernedReasoningRef(BaseModel):
    decision_id: str
    date: str
    time: str


class XAIDecisionPlaneOutput(BaseModel):
    canonical_question: CanonicalQuestion
    slot_schema: SlotSchema
    governed_reasoning: GovernedReasoningRef


# ---------------------------------------------------------------------------
# Runtime Decision Flow
# ---------------------------------------------------------------------------

class RuleEvaluation(BaseModel):
    rule_id: str
    expression: str
    left_value: float
    right_value: float
    operator: str
    result: bool


class PromoEvaluation(BaseModel):
    promo_active: bool
    promo_flags: list[str]


class DecisionOutcome(str, Enum):
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"


class RuntimeDecision(BaseModel):
    rule_evaluations: list[RuleEvaluation]
    promo_evaluation: PromoEvaluation | None = None
    outcome: DecisionOutcome
    reason: str


# ---------------------------------------------------------------------------
# Immutable Decision Records
# ---------------------------------------------------------------------------

class ImmutableDecisionRecord(BaseModel):
    decision_id: str
    date: str
    time: str
    rule: str
    outcome: DecisionOutcome
    reason: str
    trace: DecisionTraceAuthority
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Full pipeline response
# ---------------------------------------------------------------------------

class PipelineRequest(BaseModel):
    customer_id: str = "A55984"
    question: str = "Why was my transaction declined?"
    account_credit_limit: float = 5000.00
    account_current_balance: float = 4200.00
    transaction_amount: float = 950.00
    merchant_code: str = "FR8062"
    transaction_type: str = "Travel"
    product: str = "CC-Limited"
    promo_active: bool = True


class PipelineResponse(BaseModel):
    legacy_knowledge: LegacyKnowledge
    xai_plane: XAIDecisionPlaneOutput
    runtime_decision: RuntimeDecision
    immutable_record: ImmutableDecisionRecord
