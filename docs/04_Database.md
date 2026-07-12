# Database
# Database Design

# Converra AI

Version: 1.0

Status: Frozen

Database: PostgreSQL

ORM: SQLAlchemy

Migration Tool: Alembic

Primary Keys: UUID

---

# 1. Purpose

This document defines the logical and physical database design for Converra AI.

The database stores application data including organizations, users, customers, conversations, business knowledge metadata, appointments, analytics, and audit logs.

Vector embeddings are stored separately in ChromaDB, while their metadata remains in PostgreSQL.

---

# 2. Database Design Principles

Converra AI follows these principles:

- Normalize business entities.
- Keep tables focused on a single responsibility.
- Use UUID primary keys.
- Prefer foreign keys over duplicated data.
- Keep vector storage separate from relational data.
- Every table includes audit timestamps.
- Support future multi-tenancy.

---

# 3. Naming Conventions

## Table Names

snake_case

Examples

organizations

conversation_messages

knowledge_documents

---

## Column Names

snake_case

Examples

organization_id

customer_id

created_at

---

## Primary Keys

Every table uses

UUID

Example

id UUID PRIMARY KEY

---

## Timestamps

Every table contains

created_at

updated_at

---

## Soft Delete

Tables supporting deletion include

deleted_at

NULL indicates active records.

---

# 4. Entity Overview

The database is divided into the following domains.

Identity

- organizations
- users
- roles

Customer

- customers
- conversations
- messages

Knowledge

- knowledge_documents
- document_chunks
- embedding_metadata

AI

- conversation_state
- summaries
- escalations

Business

- leads
- appointments

Analytics

- feedback
- audit_logs
- llm_logs

---

# 5. Table Definitions

## organizations

Purpose

Represents a business using Converra AI.

Columns

- id
- name
- industry
- subscription_plan
- created_at
- updated_at

Relationship

One organization has many users.

One organization has many customers.

One organization has many knowledge documents.

---

## users

Purpose

Represents authenticated platform users.

Columns

- id
- organization_id
- role_id
- full_name
- email
- password_hash
- is_active
- created_at
- updated_at

Relationship

Many users belong to one organization.

---

## roles

Purpose

Stores authorization roles.

Examples

Admin

Support Agent

Manager

Owner

---

## customers

Purpose

Represents end customers interacting with AI.

Columns

- id
- organization_id
- full_name
- email
- phone
- preferred_language
- created_at

Relationship

One customer has many conversations.

---

## conversations

Purpose

Stores customer conversations.

Columns

- id
- customer_id
- current_agent
- status
- started_at
- ended_at

Relationship

One conversation contains many messages.

---

## messages

Purpose

Stores every exchanged message.

Columns

- id
- conversation_id
- sender
- message
- confidence
- timestamp

Sender values

Customer

AI

Human Agent

---

## knowledge_documents

Purpose

Uploaded PDFs or documents.

Columns

- id
- organization_id
- filename
- source
- uploaded_by
- upload_time

---

## document_chunks

Purpose

Stores document chunk metadata.

Actual embeddings remain in ChromaDB.

Columns

- id
- document_id
- chunk_number
- chunk_text
- embedding_reference

---

## embedding_metadata

Purpose

Stores metadata associated with vectors.

Columns

- id
- chunk_id
- chroma_document_id
- embedding_model

---

## conversation_state

Purpose

Stores workflow state.

Columns

- id
- conversation_id
- workflow_stage
- current_agent
- memory_snapshot

---

## summaries

Purpose

Stores AI generated summaries.

Columns

- id
- conversation_id
- customer_summary
- lead_summary
- generated_at

---

## escalations

Purpose

Stores escalated conversations.

Columns

- id
- conversation_id
- reason
- priority
- assigned_to
- status

---

## leads

Purpose

Stores qualified leads.

Columns

- id
- customer_id
- business_type
- company_size
- qualification_score
- status

---

## appointments

Purpose

Stores booked appointments.

Columns

- id
- customer_id
- appointment_date
- appointment_time
- status

---

## feedback

Purpose

Stores customer feedback.

Columns

- id
- conversation_id
- rating
- comments

---

## audit_logs

Purpose

Stores security and system events.

Examples

Login

Knowledge Upload

Escalation

Guardrail Trigger

---

## llm_logs

Purpose

Stores AI execution logs.

Columns

- id
- conversation_id
- model
- latency
- prompt_tokens
- completion_tokens
- confidence

---

# 6. Relationships

Organization

↓

Users

↓

Customers

↓

Conversations

↓

Messages

↓

Summary

One Organization

↓

Knowledge Documents

↓

Chunks

↓

Embedding Metadata

Customer

↓

Lead

↓

Appointment

Conversation

↓

Conversation State

↓

Escalation

↓

Feedback

---

# 7. Indexing Strategy

Indexes will be created on

- organization_id
- customer_id
- conversation_id
- email
- phone
- created_at
- status

Composite indexes will be added where required after profiling.

---

# 8. Data Lifecycle

Customer

↓

Conversation Created

↓

Messages Stored

↓

Workflow State Updated

↓

Summary Generated

↓

Conversation Closed

↓

Analytics Generated

↓

Archive

---

# 9. Data Retention

Conversation history shall be retained until deleted by the organization.

Audit logs shall remain immutable.

Knowledge documents may be replaced through versioning.

---

# 10. Security

Sensitive fields

- password_hash
- API keys

shall never be stored in plaintext.

JWT tokens are never stored in the database.

Uploaded documents shall be validated before processing.

---

# 11. Scalability

The schema supports:

- Multi-tenancy
- Horizontal application scaling
- Future microservice migration

The vector database is intentionally separated from PostgreSQL to improve retrieval performance.

---

# 12. Database Design Principles

The database follows:

- Third Normal Form (3NF)
- UUID primary keys
- Foreign key constraints
- High cohesion
- Low coupling
- Separation of relational and vector storage

---

# 13. Database Status

Status

Frozen (Version 1.0)