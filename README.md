# Kllama

A simple local-first chatbot built with Streamlit and Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub language count](https://img.shields.io/github/languages/count/kunalsuri/kllama)
![GitHub top language](https://img.shields.io/github/languages/top/kunalsuri/kllama?color=yellow)
![GitHub Repo stars](https://img.shields.io/github/stars/kunalsuri/kllama)

Kllama started two years ago as a teaching project to help students understand what a practical local GenAI application looks like: model selection, prompt steering, streaming responses, and privacy-preserving inference on your own machine. It is intentionally small, but it is still maintained.

That combination still matters. Before local LLM workflows became common, this project was already demonstrating a lightweight, private, and explainable path for working with generative AI in the classroom.

## Preview

![Kllama preview](docs/images/kllama-demo.svg)

This preview is a lightweight repository asset that shows the intended app shape. A live demo capture can replace it later, but it already gives future visitors immediate visual context.

## What Kllama Does

- Runs a local chat UI on top of Ollama.
- Streams model responses in real time.
- Lets you choose a local model from the sidebar.
- Supports a system prompt and basic generation controls.
- Exports the current chat as a Markdown transcript.

## Quick Start

Before creating the virtual environment, verify that your Python interpreter is 3.10 or newer:

```bash
python3 --version
```

If your `python3` command is older than 3.10, use a newer interpreter such as `python3.11` when creating the virtual environment. On older macOS installs, the default `python3` can still be 3.9.

Treat code cloned from GitHub as untrusted until you have reviewed it. Best practice is to run repositories like this inside a sandboxed environment such as a disposable virtual machine, dev container, Docker container, or at minimum a dedicated Python virtual environment that does not share packages or secrets with your main setup. Do not install dependencies globally, do not run the project with `sudo`, and avoid exposing personal tokens, SSH keys, or other sensitive files inside the sandbox.

1. Install and start Ollama from [ollama.com](https://ollama.com/).
   If your platform does not start Ollama automatically, run `ollama serve` in a separate terminal.
1. Pull at least one model.

```bash
ollama pull gemma3
ollama list
```

1. Clone the repository and create a virtual environment.

```bash
git clone https://github.com/kunalsuri/kllama.git
cd kllama
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

1. Install Kllama and its runtime dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

1. Run the app.

```bash
kllama
```

You can also use either of the direct launch commands:

```bash
python app_runner.py
streamlit run kllama.py
```

If you prefer installing from `requirements.txt`, it remains available:

```bash
python -m pip install -r requirements.txt
python app_runner.py
```

## Development

Install development dependencies with editable mode:

```bash
python -m pip install -e .[dev]
```

Run the test suite:

```bash
pytest
```

See [CHANGELOG.md](CHANGELOG.md) for the maintenance history.
See [docs/releases/0.2.0.md](docs/releases/0.2.0.md) for the prepared release notes body for the current maintenance refresh.

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

## Project Notes

- The app defaults to `http://localhost:11434` and can be pointed at another Ollama host from the UI.
- Kllama is a deliberately small codebase meant for learning and experimentation, not a full chat platform.
- The Streamlit app keeps the conversation in session state and sends the current transcript to Ollama on each turn.

## Prompt Examples

These sample prompts are intentionally student-friendly and show the kinds of local GenAI tasks Kllama was built to teach.

### Summarization

```text
Summarize the following article in 5 bullet points for an undergraduate student. Keep the language simple and include one key takeaway.
```

### Tutoring

```text
Teach me the concept of gradient descent like I am new to machine learning. Start with intuition, then give a simple numerical example.
```

### Brainstorming

```text
I want to design a student project on local LLMs. Give me 5 project ideas with learning goals, required tools, and expected difficulty.
```

### Code Explanation

```text
Explain this Python function step by step. Then tell me what could go wrong at runtime and how to improve readability.
```

### Responsible Use

```text
Review this generated answer critically. Point out possible hallucinations, missing evidence, and what I should verify before trusting it.
```

## Why This Project Still Holds Up

Kllama stays relevant because it teaches durable GenAI patterns without hiding them behind a heavyweight stack. A learner can inspect a few Python files and understand:

- local model execution,
- streamed token generation,
- prompt conditioning,
- chat state management,
- reproducible testing around pure helper logic.

That is exactly the kind of project that ages well if it is maintained.

## Next Steps

This is the current maintenance roadmap for Kllama.

1. Replace the static preview asset with a real animated demo captured from the running app.
2. Add richer multi-turn app tests that validate conversation flow and transcript export behavior.
3. Add a few small lesson-plan examples showing how Kllama can be used in class.

## Responsible AI

- Prefer local models for sensitive or educational data when possible.
- Validate generated outputs before using them in teaching, research, or decision-making workflows.
- Review the EU guidance on responsible generative AI use in research: [EU guidance](https://research-and-innovation.ec.europa.eu/news/all-research-and-innovation-news/guidelines-responsible-use-generative-ai-research-developed-european-research-area-forum-2024-03-20_en)

## AI Usage Declaration

Coding: GitHub Copilot (Pro/Enterprise), Google Antigravity, and open-weight models run via Ollama were used in Visual Studio Code to support development, primarily for code generation, completion, and debugging. All AI-assisted code was independently reviewed, tested, and refined by the authors. The authors take full responsibility for the correctness and integrity of the codebase.
