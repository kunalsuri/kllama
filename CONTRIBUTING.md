# Contributing to Kllama

Thank you for contributing.

Kllama is intentionally small. Changes should keep the project easy to read, easy to run locally, and easy to teach from.

## Before You Start

- Read [README.md](README.md) for setup, safety notes, and the release smoke test.
- Check existing issues or pull requests before starting overlapping work.
- Treat the repository as untrusted code until you have reviewed it, and work in an isolated environment.

## Local Setup

1. Make sure you are using Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install development dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

1. Install and start Ollama if you want to test the app manually.
2. Pull at least one local model such as `gemma3`.

## Development Workflow

- Keep changes focused and avoid unrelated refactors.
- Prefer small pull requests with clear intent.
- Update documentation when behavior, setup, or developer workflow changes.
- Add or update tests when changing logic that can be validated offline.
- Preserve the project's local-first and educational focus.

## Running Checks

Run the test suite before opening a pull request:

```bash
pytest
```

For a manual app check, run:

```bash
kllama
```

or:

```bash
python app_runner.py
```

## Pull Requests

When opening a pull request:

- Explain what changed and why.
- Mention any user-visible behavior changes.
- Mention any follow-up work that is intentionally out of scope.
- Confirm that tests pass locally.
- Include screenshots or terminal output when UI or setup behavior changes.

## Automation

- GitHub Actions runs the test suite for pushes and pull requests.
- Dependabot is configured to open automated dependency update pull requests for Python packages and GitHub Actions.
- Dependabot does not replace testing; its pull requests are validated by CI like any other change.

## Security

If you believe you found a security issue, do not open a public issue first. Follow the guidance in [SECURITY.md](SECURITY.md).
