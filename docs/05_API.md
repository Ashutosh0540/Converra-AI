# API
# API Design

# Converra AI

Version: 1.0

Status: Frozen

API Style: REST

Version: v1

Authentication: JWT

---

# 1. Overview

Converra AI exposes a RESTful API for communication between the frontend, AI workflow, and external systems.

All endpoints are versioned.

Base URL

/api/v1

All APIs exchange JSON.

---

# 2. API Standards

## Request Format

Content-Type

application/json

---

## Authentication

Authorization

Bearer JWT Token

---

## Response Format

Success

{
    "success": true,
    "message": "...",
    "data": {}
}

Failure

{
    "success": false,
    "message": "...",
    "error": {
        "code": "ERROR_CODE"
    }
}

---

# 3. Authentication APIs

POST

/api/v1/auth/register

Purpose

Register organization.

---

POST

/api/v1/auth/login

Purpose

Authenticate user.

---

POST

/api/v1/auth/refresh

Purpose

Refresh JWT.

---

POST

/api/v1/auth/logout

Purpose

Logout user.

---

GET

/api/v1/auth/profile

Purpose

Return authenticated user profile.

---

# 4. Organization APIs

GET

/api/v1/organizations

Return organization information.

---

PUT

/api/v1/organizations

Update organization.

---

# 5. Knowledge APIs

POST

/api/v1/knowledge/upload

Upload PDF.

---

GET

/api/v1/knowledge/documents

List uploaded documents.

---

DELETE

/api/v1/knowledge/{document_id}

Delete document.

---

POST

/api/v1/knowledge/reindex

Rebuild embeddings.

---

# 6. Customer APIs

POST

/api/v1/customers

Create customer.

---

GET

/api/v1/customers

List customers.

---

GET

/api/v1/customers/{customer_id}

Customer details.

---

PUT

/api/v1/customers/{customer_id}

Update customer.

---

# 7. Conversation APIs

POST

/api/v1/conversations

Start conversation.

---

GET

/api/v1/conversations

Conversation list.

---

GET

/api/v1/conversations/{conversation_id}

Conversation details.

---

POST

/api/v1/conversations/{conversation_id}/message

Send customer message.

---

POST

/api/v1/conversations/{conversation_id}/voice

Send voice input.

---

POST

/api/v1/conversations/{conversation_id}/close

Close conversation.

---

# 8. AI Workflow APIs

POST

/api/v1/ai/chat

Main AI endpoint.

Responsible for

- routing
- memory
- retrieval
- guardrails
- tool execution

---

POST

/api/v1/ai/summary

Generate conversation summary.

---

POST

/api/v1/ai/escalate

Escalate conversation.

---

POST

/api/v1/ai/qualify

Run lead qualification.

---

# 9. Appointment APIs

POST

/api/v1/appointments

Create appointment.

---

PUT

/api/v1/appointments/{appointment_id}

Update appointment.

---

DELETE

/api/v1/appointments/{appointment_id}

Cancel appointment.

---

GET

/api/v1/appointments

List appointments.

---

# 10. Analytics APIs

GET

/api/v1/analytics/dashboard

Dashboard statistics.

---

GET

/api/v1/analytics/conversations

Conversation metrics.

---

GET

/api/v1/analytics/escalations

Escalation metrics.

---

GET

/api/v1/analytics/agents

Agent performance.

---

# 11. Feedback APIs

POST

/api/v1/feedback

Submit customer feedback.

---

GET

/api/v1/feedback

View feedback.

---

# 12. Admin APIs

GET

/api/v1/admin/users

List users.

---

POST

/api/v1/admin/users

Create user.

---

PUT

/api/v1/admin/users/{user_id}

Update user.

---

DELETE

/api/v1/admin/users/{user_id}

Deactivate user.

---

# 13. Health APIs

GET

/api/v1/health

Application health.

---

GET

/api/v1/health/database

Database health.

---

GET

/api/v1/health/llm

LLM health.

---

GET

/api/v1/health/vector-db

Vector database health.

---

# 14. Error Codes

AUTHENTICATION_FAILED

AUTHORIZATION_FAILED

INVALID_REQUEST

RESOURCE_NOT_FOUND

PROMPT_INJECTION_DETECTED

UNSAFE_CONTENT

LLM_FAILURE

VECTOR_DB_FAILURE

DATABASE_FAILURE

TOOL_EXECUTION_FAILED

RATE_LIMIT_EXCEEDED

---

# 15. API Principles

- Stateless
- RESTful
- Versioned
- Secure
- Consistent
- JSON-only
- JWT Protected
- Fully Documented

---

# 16. Future APIs

Webhook API

Streaming API

WebSocket API

Public SDK

Marketplace API

---

# 17. API Status

Frozen (Version 1.0)