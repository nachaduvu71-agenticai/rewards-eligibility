"""Core decision engine implementing the Legacy Knowledge Extraction pipeline."""

from __future__ import annotations

from datetime import datetime

from app.models import (
    BusinessRule,
    CanonicalQuestion,
    DataField,
    DecisionOutcome,
    DecisionTraceAuthority,
    GovernedReasoningRef,
    ImmutableDecisionRecord,
    LegacyKnowledge,
    PipelineRequest,
    PipelineResponse,
    PromoEvaluation,
    RuleEvaluation,
    RuntimeDecision,
    SlotSchema,
    XAIDecisionPlaneOutput,
)

# ---------------------------------------------------------------------------
# In-memory decision record store (demo only)
# ---------------------------------------------------------------------------
_decision_store: list[ImmutableDecisionRecord] = []

_decision_counter = 0


def _next_decision_id() -> str:
    global _decision_counter
    _decision_counter += 1
    return f"CX-01-{_decision_counter:03d}"


# ---------------------------------------------------------------------------
# Stage 1 – Legacy Knowledge Extraction
# ---------------------------------------------------------------------------

def extract_legacy_knowledge() -> LegacyKnowledge:
    rules = [
        BusinessRule(
            rule_id="CB109-R3",
            condition="IF tempBalance > creditLimit",
            action="THEN DECLINE_TRANSACTION TRUE",
            description="Decline when projected balance exceeds credit limit",
        ),
        BusinessRule(
            rule_id="CB109-R5",
            condition="IF PROMO_ACTIVE AND TXN_CATEGORY != 'Travel'",
            action="THEN PROMO_ACTIVE = FALSE",
            description="Deactivate promo if transaction is not in Travel category",
        ),
    ]

    canonical_data = [
        DataField(field_name="ACCT-CREDIT-LIMIT", field_type="packed_decimal", scale=2),
        DataField(field_name="ACCT-CURRENT-BALANCE", field_type="packed_decimal", scale=2),
        DataField(field_name="TXN-AMOUNT", field_type="packed_decimal", scale=2),
        DataField(field_name="WS-TEMP-BALANCE", field_type="packed_decimal", scale=2),
        DataField(field_name="PROMO-ACTIVE-FLAG", field_type="alphanumeric", scale=None),
    ]

    trace = DecisionTraceAuthority(
        file="app/cbl/CB109.cbl",
        rule="CB109-R3",
        lines="340-355",
    )

    return LegacyKnowledge(
        business_rules=rules,
        canonical_data=canonical_data,
        decision_trace=trace,
    )


# ---------------------------------------------------------------------------
# Stage 2 – XAI Decision Plane
# ---------------------------------------------------------------------------

def build_xai_plane(req: PipelineRequest, decision_id: str) -> XAIDecisionPlaneOutput:
    now = datetime.utcnow()
    return XAIDecisionPlaneOutput(
        canonical_question=CanonicalQuestion(
            user_cx_id=req.customer_id,
            question=req.question,
        ),
        slot_schema=SlotSchema(
            time_period=now.strftime("%Y-%m"),
            product=req.product,
            merchant=req.merchant_code,
            transaction_type=req.transaction_type,
        ),
        governed_reasoning=GovernedReasoningRef(
            decision_id=decision_id,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
        ),
    )


# ---------------------------------------------------------------------------
# Stage 3 – Runtime Decision Flow
# ---------------------------------------------------------------------------

def evaluate_rules(req: PipelineRequest) -> RuntimeDecision:
    temp_balance = req.account_current_balance + req.transaction_amount

    credit_check = RuleEvaluation(
        rule_id="CB109-R3",
        expression="TEMP_BALANCE > ACCT-CREDIT-LIMIT",
        left_value=temp_balance,
        right_value=req.account_credit_limit,
        operator=">",
        result=temp_balance > req.account_credit_limit,
    )

    promo_eval = None
    if req.promo_active:
        promo_flags = ["CARD_ACTIVE", "REWARDS_ENROLLED", "CATEGORY_MATCH"]
        if req.transaction_type != "Travel":
            promo_flags = ["CARD_ACTIVE", "REWARDS_ENROLLED"]
        promo_eval = PromoEvaluation(promo_active=req.promo_active, promo_flags=promo_flags)

    if credit_check.result:
        outcome = DecisionOutcome.DECLINE
        reason = (
            f"Projected balance ${temp_balance:,.2f} exceeds "
            f"credit limit ${req.account_credit_limit:,.2f}"
        )
    else:
        outcome = DecisionOutcome.APPROVE
        reason = (
            f"Projected balance ${temp_balance:,.2f} is within "
            f"credit limit ${req.account_credit_limit:,.2f}"
        )

    return RuntimeDecision(
        rule_evaluations=[credit_check],
        promo_evaluation=promo_eval,
        outcome=outcome,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Stage 4 – Immutable Decision Record
# ---------------------------------------------------------------------------

def create_immutable_record(
    decision_id: str,
    runtime: RuntimeDecision,
    trace: DecisionTraceAuthority,
) -> ImmutableDecisionRecord:
    now = datetime.utcnow()
    record = ImmutableDecisionRecord(
        decision_id=decision_id,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        rule=trace.rule,
        outcome=runtime.outcome,
        reason=runtime.reason,
        trace=trace,
    )
    _decision_store.append(record)
    return record


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    decision_id = _next_decision_id()

    legacy = extract_legacy_knowledge()
    xai = build_xai_plane(req, decision_id)
    runtime = evaluate_rules(req)
    record = create_immutable_record(decision_id, runtime, legacy.decision_trace)

    return PipelineResponse(
        legacy_knowledge=legacy,
        xai_plane=xai,
        runtime_decision=runtime,
        immutable_record=record,
    )


def get_decision_records() -> list[ImmutableDecisionRecord]:
    return list(_decision_store)
