# AI Workflow
# AI Workflow Design

# Converra AI

Version: 1.0

Status: Frozen

Workflow Engine: LangGraph

Architecture: Multi-Agent Workflow

---

# 1. Purpose

This document defines the AI orchestration workflow of Converra AI.

The workflow coordinates all AI components including routing, memory, knowledge retrieval, tool execution, guardrails, and response generation.

Every customer interaction follows the workflow defined in this document.

---

# 2. AI Philosophy

Converra AI follows five AI principles.

1. Trust before Intelligence
2. Retrieval before Generation
3. Human-in-the-loop
4. Explainable Decisions
5. Modular Agent Collaboration

---

# 3. High-Level Workflow

Customer Request

↓

Input Guardrails

↓

Conversation Memory

↓

Intent Router

↓

Knowledge Retrieval (if required)

↓

Workflow Planner

↓

Agent Execution

↓

Tool Execution (if required)

↓

Output Guardrails

↓

Memory Update

↓

Logging

↓

Customer Response

---

# 4. Workflow Stages

The workflow consists of eleven stages.

Stage 1

Receive Request

Input from

- Chat
- Voice
- API

---

Stage 2

Input Validation

Validate

- Empty requests
- Invalid payloads
- Prompt injection
- File limits
- Authentication

---

Stage 3

Conversation Memory

Retrieve

- Previous conversations
- Customer profile
- Preferences
- Workflow stage
- Existing appointments

---

Stage 4

Intent Classification

Determine customer intent.

Examples

FAQ

Appointment

Complaint

Sales

Greeting

Medical

Unknown

---

Stage 5

Knowledge Retrieval

Retrieve relevant business knowledge.

Pipeline

Knowledge Base

↓

Vector Search

↓

Top K Documents

↓

Context Builder

↓

Agent

---

Stage 6

Workflow Planning

Determine

- Which agent should execute
- Whether tool calling is required
- Whether escalation is likely

---

Stage 7

Agent Execution

Available agents

FAQ Agent

Qualification Agent

Scheduling Agent

Escalation Agent

Summary Agent

Only one primary agent executes per workflow cycle.

---

Stage 8

Tool Execution

Agents may request tools.

Examples

Google Calendar

Email

CRM

Notifications

Database

All tool requests require authorization.

---

Stage 9

Output Validation

Validate

- Hallucinations
- Unsafe outputs
- Policy violations
- Missing citations
- Invalid JSON

---

Stage 10

Memory Update

Store

Conversation

Summary

Customer profile

Preferences

Workflow stage

Lead information

---

Stage 11

Logging

Store

Latency

Prompt tokens

Completion tokens

Confidence

Retrieved documents

Executed tools

Errors

---

# 5. AI Agents

## FAQ Agent

Responsibilities

- Answer customer questions
- Use retrieved knowledge
- Refuse unsupported requests

---

## Qualification Agent

Responsibilities

- Collect lead information
- Score leads
- Update CRM

---

## Scheduling Agent

Responsibilities

- Book appointments
- Modify appointments
- Cancel appointments

---

## Escalation Agent

Responsibilities

- Detect unsafe situations
- Transfer conversations
- Generate escalation reason

---

## Summary Agent

Responsibilities

- Generate conversation summary
- Generate CRM notes
- Recommend next action

---

# 6. Shared Conversation State

The workflow shares a common state.

Fields

Conversation ID

Customer ID

Organization ID

Current Workflow Stage

Current Agent

Conversation History

Retrieved Documents

Memory

Lead Information

Escalation Status

Tool Results

Final Response

---

# 7. Agent Communication Rules

Agents never communicate directly.

Allowed

Agent

↓

Workflow

↓

Next Agent

Forbidden

FAQ

↓

Scheduling

Qualification

↓

Escalation

Agents remain independent.

---

# 8. Tool Calling

The workflow decides

WHEN

The agent decides

WHICH TOOL

The backend executes

THE TOOL

The AI never executes external APIs directly.

---

# 9. Memory Strategy

Short-Term Memory

Current conversation.

---

Long-Term Memory

Customer profile.

Previous appointments.

Preferences.

Conversation summaries.

Lead history.

---

# 10. Knowledge Retrieval Strategy

Pipeline

Customer Question

↓

Embedding

↓

Vector Search

↓

Top K Chunks

↓

Re-ranking

↓

Context Builder

↓

LLM

The LLM never searches documents directly.

---

# 11. Escalation Strategy

Escalation occurs when

Medical advice

Legal advice

Low confidence

Human request

High customer frustration

Repeated failures

Sensitive business actions

---

# 12. Error Recovery

If any workflow stage fails

↓

Log Error

↓

Fallback Response

↓

Escalate if required

↓

Preserve Conversation

The workflow never crashes.

---

# 13. AI Decision Logging

Every workflow stores

Intent

Selected Agent

Retrieved Documents

Confidence

Tool Calls

Escalation

Latency

Model Used

Memory Updates

---

# 14. Workflow Completion

A workflow cycle completes after

Response generated

↓

Memory updated

↓

Logs stored

↓

Response delivered

---

# 15. Future Workflow Extensions

Parallel Agent Execution

Reflection Agent

Critic Agent

Planning Agent

Autonomous Agent Collaboration

These are outside the MVP.

---

# 16. Workflow Status

Frozen (Version 1.0)