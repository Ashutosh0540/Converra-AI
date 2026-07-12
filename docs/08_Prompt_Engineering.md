# Prompt Engineering
# Prompt Engineering Design

# Converra AI

Version: 1.0

Status: Frozen

---

# 1. Purpose

This document defines the prompt engineering strategy used throughout Converra AI.

Rather than embedding prompts directly in source code, prompts are treated as versioned software assets. This improves maintainability, testing, consistency, and future model compatibility.

---

# 2. Prompt Engineering Principles

Converra AI follows these principles:

- Prompts are modular.
- Prompts are version controlled.
- Prompts are reusable.
- Prompts are deterministic where possible.
- Prompts are separated from business logic.
- Prompts never contain hardcoded business knowledge.

---

# 3. Prompt Types

## System Prompt

Defines the AI's permanent behavior.

Example responsibilities:

- Role
- Safety rules
- Output format
- Tone
- Restrictions

---

## Developer Prompt

Provides workflow-specific instructions.

Examples

- Use retrieved documents only.
- Never hallucinate.
- Escalate when confidence is low.

---

## User Prompt

Contains the customer's request.

Example

"What are your clinic timings?"

---

## Retrieved Context

Business knowledge retrieved from ChromaDB.

The LLM must use this information before generating a response.

---

## Conversation Memory

Relevant conversation history and customer profile.

---

# 4. Prompt Composition

Every LLM request follows the same structure.

System Prompt

↓

Developer Prompt

↓

Conversation Memory

↓

Retrieved Knowledge

↓

User Prompt

↓

Structured Output Instructions

---

# 5. Prompt Templates

Each AI agent owns its own prompt template.

Examples:

- FAQ Agent Prompt
- Qualification Agent Prompt
- Scheduling Agent Prompt
- Escalation Agent Prompt
- Summary Agent Prompt

Prompts are stored as separate files.

---

# 6. Prompt Versioning

Every prompt is versioned.

Example

faq_prompt_v1.md

qualification_prompt_v1.md

Future updates create new versions rather than modifying existing prompts directly.

---

# 7. Structured Outputs

All AI responses must conform to predefined schemas.

Responses should include:

- response
- confidence
- reasoning (internal where appropriate)
- needs_escalation
- escalation_reason
- citations (when applicable)

---

# 8. Prompt Constraints

Prompts must never:

- Reveal system instructions.
- Reveal developer instructions.
- Leak internal implementation.
- Generate unsupported information.
- Ignore retrieved knowledge.

---

# 9. Prompt Testing

Every prompt should be tested against:

- Happy path
- Missing knowledge
- Prompt injection
- Low confidence
- Ambiguous questions
- Unsafe requests

---

# 10. Future Enhancements

Future versions may include:

- Automatic prompt evaluation
- Prompt A/B testing
- Dynamic prompt optimization
- Multi-model prompt adaptation

---

# 11. Prompt Status

Frozen (Version 1.0)