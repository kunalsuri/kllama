# Maintaining Kllama

This guide is for contributors and maintainers working on the repository itself.

## Development

Install development dependencies with editable mode:

```bash
python -m pip install -e .[dev]
```

Run the local verification suite:

```bash
ruff check .
pytest
python -m build --sdist --wheel
```

See [../CHANGELOG.md](../CHANGELOG.md) for the maintenance history.
See [releases/0.2.0.md](releases/0.2.0.md) for the prepared release notes body for the current maintenance refresh.

## Community and Support

- Read [../CONTRIBUTING.md](../CONTRIBUTING.md) before opening a pull request.
- Review [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) for participation expectations.
- Follow [../SECURITY.md](../SECURITY.md) for vulnerability reporting.
- Dependabot is configured to open dependency update pull requests, and GitHub Actions CI runs tests for pushes and pull requests.

## Release Smoke Test

Before publishing a release, run one live manual smoke test against a real local Ollama instance:

1. Start Ollama and confirm the server is reachable.
2. Pull a test model such as `gemma3` if it is not already installed.
3. Create a fresh virtual environment and install the project with `python -m pip install -e .[dev]`.
4. Launch the app with `kllama` or `python app_runner.py`.
5. Confirm that the model appears in the sidebar and can be selected.
6. Send a simple prompt and verify that the response streams back successfully.
7. Download a transcript and confirm the generated Markdown file contains the conversation metadata and messages.
8. Run `ruff check .`, `pytest`, and `python -m build --sdist --wheel` and confirm they all pass.

## Repository Layout

The top-level repository is intentionally small. New users usually only need to care about the following paths:

- `kllama.py`: main Streamlit app.
- `kllama_core.py`: pure helper logic for payload building, model parsing, and transcript export.
- `app_runner.py`: lightweight launcher used by the installed `kllama` command.
- `tests/`: offline pytest suite for app and helper behavior.
- `docs/images/`: README preview assets.
- `docs/releases/`: release notes and maintenance artifacts.
- `.github/workflows/`: CI automation.
- `.devcontainer/`: optional containerized development setup.
- `.vscode/`: workspace settings for local development in VS Code.

Local folders such as `.venv/`, `.pytest_cache/`, `.mypy_cache/`, and `__pycache__/` are generated during development and can be ignored or safely deleted when you want a cleaner workspace.

## Next Steps

This is the current maintenance roadmap for Kllama.

1. Replace the static preview asset with a real animated demo captured from the running app.
2. Add richer multi-turn app tests that validate conversation flow and transcript export behavior.
3. Add a few small lesson-plan examples showing how Kllama can be used in class.
