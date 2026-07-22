from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from app.models.enums import AgentType

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"reveal\s+the\s+system\s+prompt",
    r"bypass\s+policy",
    r"execute\s+hidden\s+commands",
]

SENSITIVE_PATTERNS = {
    "medical": [r"\bmedical\b", r"\bdiagnos", r"\btreatment\b", r"\bsymptom\b"],
    "financial": [r"\bfinancial\b", r"\binvest", r"\bloan\b", r"\bstock\b"],
    "legal": [r"\blegal\b", r"\blawyer\b", r"\blawsuit\b", r"\bcontract\b"],
}

ESCALATION_PATTERNS = [
    r"\bhuman\b",
    r"\brepresentative\b",
    r"\bagent\b",
    r"\bsupervisor\b",
]

SUMMARY_PATTERNS = [r"\bbye\b", r"\bthanks\b", r"\bclose\b", r"\bend chat\b"]

FAQ_PATTERNS = [
    r"\bwhat\b",
    r"\bhow\b",
    r"\bwhere\b",
    r"\bwhen\b",
    r"\bwhy\b",
    r"\bfaq\b",
    r"\bsupport\b",
]

LEAD_PATTERNS = [
    r"\bprice\b",
    r"\bpricing\b",
    r"\bquote\b",
    r"\bbudget\b",
    r"\bdemo\b",
    r"\bsales\b",
    r"\bcost\b",
]

SCHEDULING_PATTERNS = [
    r"\bappointment\b",
    r"\bschedule\b",
    r"\bmeeting\b",
    r"\bbook\b",
    r"\breschedule\b",
]


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    reason: Optional[str] = None
    escalation_required: bool = False


class GuardrailService:
    def check_input(self, message: str) -> GuardrailDecision:
        normalized = message.lower().strip()
        if not normalized:
            return GuardrailDecision(
                allowed=False,
                reason="Message cannot be empty.",
                escalation_required=False,
            )

        if self._matches_any(normalized, PROMPT_INJECTION_PATTERNS):
            return GuardrailDecision(
                allowed=False,
                reason="Prompt injection attempt detected.",
                escalation_required=True,
            )

        if self._matches_any(normalized, ESCALATION_PATTERNS):
            return GuardrailDecision(
                allowed=True,
                reason="Human escalation requested.",
                escalation_required=True,
            )

        for label, patterns in SENSITIVE_PATTERNS.items():
            if self._matches_any(normalized, patterns):
                return GuardrailDecision(
                    allowed=True,
                    reason=f"{label.title()} advice must be escalated.",
                    escalation_required=True,
                )

        return GuardrailDecision(allowed=True)

    def classify_intent(self, message: str, has_relevant_knowledge: bool) -> AgentType:
        normalized = message.lower().strip()
        if self._matches_any(normalized, SUMMARY_PATTERNS):
            return AgentType.SUMMARY

        if self._matches_any(normalized, SCHEDULING_PATTERNS):
            return AgentType.SCHEDULING

        if self._matches_any(normalized, LEAD_PATTERNS):
            return AgentType.LEAD

        if has_relevant_knowledge or self._matches_any(normalized, FAQ_PATTERNS):
            return AgentType.FAQ

        return AgentType.ESCALATION

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        return any(
            re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns
        )
