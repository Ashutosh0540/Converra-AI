# System Architecture

The Next.js dashboard communicates with the FastAPI application through authenticated REST APIs and WebSockets. FastAPI uses service and repository layers over PostgreSQL, Chroma for vector retrieval, and dedicated voice/session services. The orchestration service routes messages through FAQ, lead, scheduling, summary, and escalation agents. HITL records cases and audit events transactionally with conversation state.

Production traffic reaches the frontend and backend independently. The backend exposes liveness, readiness, version, and Prometheus-compatible metrics endpoints. PostgreSQL and Chroma data use persistent volumes.
