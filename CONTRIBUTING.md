# Contributing

Create a branch, install backend dependencies with `pip install -r backend/requirements-dev.txt` and frontend dependencies with `npm ci`, then install hooks with `pre-commit install`. Before opening a pull request run `ruff check`, `black --check`, `isort --check-only`, `pytest`, `npm run typecheck`, and `npm run build`. Include migrations for persistent model changes and tests for new behavior.
