# Changelog

All notable changes to Kllama will be documented in this file.

The project began earlier as a lightweight teaching tool for local GenAI workflows. Formal changelog tracking starts with the current maintenance refresh.

## [Unreleased]

### Unreleased Added

- A repository-hosted SVG preview asset for the README.
- An interactive mocked Streamlit app test that submits a chat prompt and validates a streamed response.
- Dependabot configuration for Python dependencies and GitHub Actions.

### Unreleased Changed

- Updated the README roadmap to reflect completed maintenance items and remaining next steps.
- Expanded CI to test Python 3.14 in addition to earlier supported versions.

## [0.2.0] - 2026-03-08

Release notes draft: `docs/releases/0.2.0.md`

### Added

- Packaging metadata in `pyproject.toml`.
- A pure helper module for chat payloads, model parsing, and transcript export.
- A pytest-based test suite for offline validation.
- A mocked Streamlit app smoke test scaffold.
- GitHub Actions CI across supported Python versions.
- VS Code workspace settings that point to the local virtual environment.
- A `Next Steps` roadmap in the README.
- Curated prompt examples for students and practitioners.

### Changed

- Refactored the Streamlit app to use a cleaner Ollama client flow.
- Added model refresh, system prompt controls, generation settings, and transcript download.
- Improved project documentation to better explain the educational purpose and maintenance status.
- Updated dependency constraints for current Streamlit and Ollama releases.
- Improved the launcher script to run Streamlit through the active Python interpreter.

### Removed

- Deleted the ad hoc local test script that depended on a live Ollama instance.
- Removed the tracked placeholder secrets file from the repository.
