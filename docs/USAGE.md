# Using Kllama

This guide is for people who want to understand how Kllama is intended to be used after setup.

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
