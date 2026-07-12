# Architecture Decision Log (ADR)

# Converra AI

Version: 1.0

Status: Frozen

---

# ADR-001

Decision

Enterprise AI Agent Platform

Status

Accepted

Reason

Reusable platform supporting multiple AI agents.

---

# ADR-002

Decision

Modular Monolith

Status

Accepted

Reason

Simpler development while maintaining clear module boundaries and future migration capability.

Trade-offs

Pros

- Easier debugging
- Faster development
- Lower infrastructure cost

Cons

- Single deployment
- Shared database

---

# ADR-003

Decision

FastAPI Backend

Status

Accepted

Reason

High performance, async support, excellent Python ecosystem.

Alternatives

- Flask
- Django

---

# ADR-004

Decision

Next.js Frontend

Status

Accepted

Reason

Modern React framework with scalability.

---

# ADR-005

Decision

LangGraph

Status

Accepted

Reason

Explicit workflow orchestration and state management.

Alternatives

- Manual Routing
- CrewAI
- AutoGen

---

# ADR-006

Decision

PostgreSQL

Status

Accepted

Reason

Reliable relational database with strong ecosystem.

Alternatives

- MongoDB
- MySQL

---

# ADR-007

Decision

ChromaDB

Status

Accepted

Reason

Open-source vector database suitable for local development.

Alternatives

- Pinecone
- Weaviate
- FAISS

---

# ADR-008

Decision

Groq as Initial LLM

Status

Accepted

Reason

Free API for development.

Future

Provider abstraction allows switching providers.

---

# ADR-009

Decision

LLM Abstraction Layer

Status

Accepted

Reason

Avoid vendor lock-in.

Supports

- Groq
- OpenAI
- Anthropic

---

# ADR-010

Decision

UUID Primary Keys

Status

Accepted

Reason

Production-ready identifiers.

---

# ADR-011

Decision

RAG Architecture

Status

Accepted

Reason

Ground AI responses using business knowledge.

---

# ADR-012

Decision

Human-in-the-loop

Status

Accepted

Reason

Critical business actions require human oversight.

---

# ADR-013

Decision

Retrieval Before Generation

Status

Accepted

Reason

Minimize hallucinations.

---

# ADR-014

Decision

Prompt Versioning

Status

Accepted

Reason

Treat prompts as maintainable software assets.

---

# ADR-015

Decision

Guardrails

Status

Accepted

Reason

Enterprise-grade AI safety.

---

# ADR-016

Decision

API Versioning

Status

Accepted

Reason

Backward compatibility.

Convention

/api/v1/

---

# ADR Status

Frozen (Version 1.0)