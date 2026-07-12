# Architecture
# System Architecture

# Converra AI

Version: 1.0

Status: Frozen

Architecture Style: Modular Monolith

---

# 1. Introduction

This document describes the high-level and low-level architecture of Converra AI.

Converra AI is designed as a Modular Monolith to balance development simplicity with production-grade software engineering practices. Each module has a single responsibility and communicates through well-defined interfaces, enabling future migration to microservices if required.

---

# 2. Architectural Goals

The architecture is designed to achieve the following goals:

- Modularity
- Scalability
- Maintainability
- Reliability
- Explainability
- Security
- Testability
- AI Safety

---

# 3. Architecture Style

Converra AI follows the Modular Monolith architecture.

Characteristics:

- Single deployable application
- Shared PostgreSQL database
- Independent modules
- Loose coupling
- High cohesion
- Clear module boundaries

Future versions may separate modules into independent microservices without changing business logic.

---

# 4. High-Level Architecture

```

```
                User
                  │
                  ▼
        Next.js Frontend
                  │
                  ▼
            FastAPI Backend
                  │
                  ▼
        Authentication Layer
                  │
                  ▼
       Workflow Orchestrator
                  │
                  ▼
         Conversation State
                  │
      ┌───────────┼────────────┐
      │           │            │
      ▼           ▼            ▼
 Knowledge     AI Agents    Tool Service
 Service                      │
      │                       ▼
      ▼                External APIs
 ChromaDB
      │
      ▼
 Business Documents

```

```markdown

---

# 5. Module Architecture

The backend is divided into independent modules.

## API Module

Responsibilities:

- HTTP endpoints
- Request validation
- Response serialization

---

## Authentication Module

Responsibilities:

- JWT authentication
- User authorization
- Role management

---

## Workflow Orchestrator

Responsibilities:

- Workflow execution
- Routing
- Agent selection
- State coordination

---

## Knowledge Module

Responsibilities:

- Document upload
- PDF parsing
- Chunking
- Embeddings
- Retrieval
- Citation generation

---

## AI Agents

Responsibilities:

- FAQ Agent
- Qualification Agent
- Scheduling Agent
- Escalation Agent
- Summary Agent

Each agent performs a single business function.

---

## Memory Module

Responsibilities:

- Conversation history
- Long-term memory
- Customer profile
- Session state

---

## Tool Module

Responsibilities:

- Calendar
- Email
- CRM
- Notifications

---

## Guardrail Module

Responsibilities:

- Prompt injection detection
- Output validation
- Policy enforcement
- Tool authorization

---

## Analytics Module

Responsibilities:

- Conversation analytics
- AI metrics
- Business metrics
- Dashboard data

---

## Logging Module

Responsibilities:

- Request logs
- AI logs
- Tool execution logs
- Error logs
- Audit logs

---

# 6. Module Dependency Rules

Modules may only communicate through public interfaces.

Allowed dependencies:

API
↓

Workflow

Workflow
↓

Agents

Agents
↓

Knowledge

Agents
↓

Memory

Agents
↓

Tools

Guardrails
↓

All AI outputs

Forbidden:

❌ Agent → Database directly

❌ Frontend → Database

❌ Agent → Agent

❌ Tool → Workflow

This keeps coupling low.

---

# 7. Request Lifecycle

A typical customer request follows this lifecycle:

Customer

↓

Frontend

↓

FastAPI

↓

Authentication

↓

Guardrails (Input)

↓

Workflow Orchestrator

↓

Conversation State

↓

Knowledge Retrieval

↓

Agent Execution

↓

Tool Execution (if required)

↓

Output Guardrails

↓

Logging

↓

Frontend Response

---

# 8. AI Workflow

Every AI interaction follows the same workflow.

1. Receive customer input.

2. Validate input.

3. Retrieve conversation state.

4. Detect intent.

5. Retrieve business knowledge.

6. Execute selected AI agent.

7. Validate output.

8. Execute tools if authorized.

9. Update memory.

10. Generate response.

11. Log interaction.

---

# 9. Design Patterns

The following software design patterns are used.

### Factory Pattern

Creates AI agents.

---

### Strategy Pattern

Different agent behaviors.

---

### Repository Pattern

Database abstraction.

---

### Dependency Injection

Loose coupling.

---

### Service Layer

Business logic separation.

---

### Adapter Pattern

External API integrations.

---

### State Pattern

Conversation workflow management.

---

# 10. Error Handling Strategy

The platform shall never expose internal errors.

Instead:

- log the exception
- generate user-friendly response
- maintain workflow consistency
- preserve conversation state

---

# 11. Logging Strategy

Every important event is logged.

Examples:

- User login
- Conversation start
- Knowledge retrieval
- Tool execution
- Escalation
- Prompt injection attempt
- LLM response
- Errors

---

# 12. Security Architecture

Security layers include:

- JWT Authentication
- Role-Based Access Control
- Prompt Injection Detection
- Tool Authorization
- Output Validation
- Secure Secret Management

---

# 13. Scalability Strategy

Although implemented as a Modular Monolith, every module is designed to become an independent microservice.

Examples:

Current:

Knowledge Module

Future:

Knowledge Service

This minimizes future migration effort.

---

# 14. Architectural Principles

Converra AI follows these principles:

- Single Responsibility Principle
- Separation of Concerns
- Dependency Inversion
- High Cohesion
- Loose Coupling
- Human-in-the-loop
- Retrieval before Generation
- Trust before Intelligence

---

# 15. Architecture Decision

Architecture Style:

✅ Modular Monolith

Reason:

- Faster development
- Easier testing
- Simpler deployment
- Clear module boundaries
- Supports future migration to microservices

Status:

Frozen (Version 1.0)