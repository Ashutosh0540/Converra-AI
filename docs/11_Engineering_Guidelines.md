# Engineering Guidelines

# Converra AI

Version: 1.0

Status: Frozen

---

# 1. Purpose

This document defines the engineering standards followed throughout Converra AI.

These guidelines ensure consistency, maintainability, readability, and production readiness.

---

# 2. Coding Principles

Every module should follow

- Single Responsibility Principle
- Separation of Concerns
- Dependency Injection
- High Cohesion
- Low Coupling

---

# 3. Python Standards

- Python 3.12+
- PEP 8
- Ruff
- Black
- Type Hints Required
- Docstrings for public methods

---

# 4. Folder Organization

Each folder owns one responsibility.

Examples

agents/

knowledge/

memory/

guardrails/

database/

api/

services/

No business logic inside API routes.

---

# 5. Naming Conventions

Files

snake_case.py

Classes

PascalCase

Functions

snake_case

Constants

UPPER_CASE

Variables

snake_case

---

# 6. Error Handling

Never expose internal exceptions.

Return meaningful API responses.

Always log exceptions.

Use custom exception classes.

---

# 7. Logging

Every module logs

- Start
- Success
- Failure

Never log

- Passwords
- API Keys
- Sensitive customer data

---

# 8. Database

Use SQLAlchemy ORM.

No raw SQL unless necessary.

Every migration via Alembic.

---

# 9. API Standards

RESTful

Versioned

JWT Protected

Consistent response format

---

# 10. AI Standards

All AI responses must

- Use retrieved context
- Pass guardrails
- Follow JSON schema
- Include confidence score
- Support escalation

---

# 11. Testing

Every feature requires

- Unit Tests
- Integration Tests

Future

End-to-End Tests

---

# 12. Git Workflow

Main Branch

main

Development Branch

develop

Feature Branches

feature/<feature-name>

Bug Fixes

fix/<bug-name>

---

# 13. Commit Convention

Examples

feat: add knowledge upload

fix: conversation state bug

docs: update architecture

refactor: simplify workflow

test: add authentication tests

---

# 14. Documentation

Every module should include

- Purpose
- Inputs
- Outputs
- Dependencies

Complex workflows require diagrams.

---

# 15. Code Review Checklist

Before merging

- Tests pass
- Documentation updated
- Logging added
- Error handling implemented
- Type hints present
- No hardcoded secrets

---

# 16. Definition of Done

A feature is complete when

- Functional
- Tested
- Logged
- Documented
- Secure
- Review Approved

---

# Engineering Status

Frozen (Version 1.0)