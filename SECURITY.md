# Security Policy

## Supported Versions

Security fixes are expected only for the latest code on `main` and the most recent tagged release.

Older snapshots, forks, and unmaintained local modifications should be treated as unsupported.

## Reporting a Vulnerability

If you discover a security vulnerability:

1. Do not publish the details in a public GitHub issue before a fix is available.
2. Use GitHub private vulnerability reporting for this repository if it is enabled.
3. If private reporting is not available, contact the maintainer directly through GitHub.
4. Include a clear description, affected files or workflow, reproduction steps, impact, and any suggested mitigation.

## What to Report

Examples include:

- Exposure of secrets, tokens, or sensitive local files.
- Unsafe execution behavior that could affect a user's machine or data.
- Dependency issues with realistic security impact.
- Sandbox escape or unsafe setup guidance that could lead to system compromise.

## Response Expectations

The goal is to acknowledge reports promptly, validate impact, prepare a fix, and disclose details responsibly after mitigation is available.

## User Safety Notes

Because Kllama is a local-first application, users should continue following the setup guidance in [README.md](README.md):

- Use an isolated environment.
- Avoid running the project with elevated privileges.
- Avoid exposing private credentials or sensitive local files during testing.
