from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    AGENT = "AGENT"
    VIEWER = "VIEWER"


class DocumentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class AgentType(str, Enum):
    FAQ = "FAQ"
    LEAD = "LEAD"
    SCHEDULING = "SCHEDULING"
    SUMMARY = "SUMMARY"
    ESCALATION = "ESCALATION"


class ConversationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class WorkflowStage(str, Enum):
    ROUTING = "ROUTING"
    RETRIEVAL = "RETRIEVAL"
    EXECUTION = "EXECUTION"
    VALIDATION = "VALIDATION"
    MEMORY_UPDATE = "MEMORY_UPDATE"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class EscalationStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class EscalationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationActionType(str, Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    REASSIGNED = "REASSIGNED"
    ACCEPTED = "ACCEPTED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    TRANSFERRED = "TRANSFERRED"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    OVERRIDE = "OVERRIDE"
