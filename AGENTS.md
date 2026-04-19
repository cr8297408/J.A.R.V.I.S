# AGENTS.md — J.A.R.V.I.S. Agent Instructions

> This file governs how AI agents (Claude Code, sub-agents, SDD phases) work on this codebase.
> **All agents MUST read this file before writing any code.**

---

## 1. Project Identity

**J.A.R.V.I.S.** is a voice-first programming CLI. The user speaks; Jarvis acts.
Latency is the primary constraint. Every architectural decision must be measured against it.

- **Language**: Python 3.10+
- **Entry point**: `jarvis` CLI (click), installed via `pyproject.toml`
- **Backends**: Claude API (primary), Gemini API, Groq (fallback)
- **Key non-goal**: Do NOT add features not in the roadmap (`docs/ROADMAP_VOICE_CLI.md`)

---

## 2. Module Map & Ownership

```
jarvis/          ← CLI surface (click commands only — no business logic here)
core/
  audio/         ← VAD, microphone capture, barge-in
  server/        ← Daemon mode, TCP server, queue management
  cli/           ← PTY wrapper (legacy mode)
  lexer/         ← Intent pre-classifier, token parsing
  integration/   ← PoC files (do not depend on these in production code)
adapters/
  llm/           ← LLM backends (Claude, Gemini, Groq, OpenRouter)
  stt/           ← Speech-to-text (MLX Whisper, Ghost Typer)
  tts/           ← Text-to-speech (Edge TTS, mac_say)
hooks/           ← Gemini CLI hooks (after_model, notification)
apps/            ← Landing page (TypeScript/React — separate scope)
docs/            ← Architecture docs and roadmap (read-only for agents)
```

---

## 3. Scope Rules

These rules define what agents are **allowed** to touch in each area.
Violating scope requires explicit user approval — never assume it.

### 3.1 `jarvis/` — CLI Layer

**Allowed**: click command definitions, option parsing, env validation, `--help` text, routing to `core/` or `adapters/`.

**Forbidden**:
- Business logic (move it to `core/`)
- Direct imports from `adapters/` (go through `core/` interfaces)
- Audio, LLM, or STT calls

**Pattern**: Each command must be thin — validate, delegate, report.

---

### 3.2 `core/` — Domain Logic

**Allowed**: Orchestration of audio pipeline, daemon lifecycle, intent classification, PTY management.

**Forbidden**:
- Direct SDK calls to Anthropic, Gemini, or Groq (use `adapters/llm/`)
- Direct calls to pyaudio from outside `core/audio/`
- Blocking calls in the audio hot path (see §6 Latency Rules)

**Pattern**: `core/` modules define WHAT happens. `adapters/` define HOW via external SDKs.

**Dependency direction**: `jarvis/` → `core/` → `adapters/`. Never reverse.

---

### 3.3 `adapters/` — External Integrations

**Allowed**: SDK initialization, API calls, response parsing, retry logic, streaming.

**Forbidden**:
- Imports from `core/` (adapters must be standalone and testable in isolation)
- Stateful singletons (use dependency injection from `core/`)
- Catching all exceptions silently — always propagate or log with context

**Naming convention**:
- LLM adapters: `{provider}_adapter.py` or `{provider}_{role}.py`
- STT adapters: `{engine}_stt.py`
- TTS adapters: `{engine}_tts.py`

**Interface contract**: Every LLM adapter must expose:
```python
def stream_response(prompt: str, context: list[dict]) -> Iterator[str]: ...
def summarize_for_voice(text: str) -> str: ...
```

Every TTS adapter must expose:
```python
def speak(text: str) -> None: ...
def speak_streaming(token_iter: Iterator[str]) -> None: ...
```

---

### 3.4 `hooks/` — Gemini CLI Hooks

**Scope**: Gemini CLI integration hooks only. These are standalone scripts invoked by the Gemini CLI process.

**Forbidden**:
- Importing from `core/` or `adapters/` directly (hooks run in a separate process)
- Heavy dependencies (keep startup time < 100ms)

---

### 3.5 `apps/` — Landing Page

**Scope**: TypeScript/React/Vite only. Fully isolated from the Python backend.

**Forbidden**: Any Python file inside `apps/`. Any `apps/` import from Python code.

---

### 3.6 `docs/` — Documentation

**Read-only for agents** unless the task explicitly says to update docs.
Never modify `docs/ROADMAP_VOICE_CLI.md` unless updating issue status.

---

## 4. Architecture Constraints

### 4.1 Layering (enforce strictly)

```
CLI (jarvis/) ──→ Domain (core/) ──→ Infrastructure (adapters/)
                      ↑
                  No reverse imports
```

If an adapter needs to call back into core logic, use a callback/protocol passed at construction time — never import `core/` from `adapters/`.

### 4.2 Interface-First Development

Before implementing a new adapter, define the interface (Protocol class) in `core/`.
Adapters implement the interface. `core/` imports the Protocol, not the concrete class.

```python
# core/interfaces.py
from typing import Protocol, Iterator

class LLMAdapter(Protocol):
    def stream_response(self, prompt: str, context: list[dict]) -> Iterator[str]: ...
```

### 4.3 Configuration via Environment

All runtime config (API keys, engine selection, timeouts) comes from environment variables.
Use `os.getenv()` with explicit defaults. Never hardcode API keys or model names.

Active backend selected by `ACTIVE_BRAIN_ENGINE` env var (`claude` | `gemini` | `groq`).

### 4.4 No Shared Mutable State

Audio pipeline, daemon, and CLI run in separate threads/processes.
Communication via queues (`queue.Queue`) only. No module-level mutable globals.

---

## 5. Coding Conventions

### Python

- **Style**: Ruff (`ruff check`, `ruff format`). Line length: 100.
- **Type hints**: Required on all public functions and class methods.
- **Docstrings**: Only on public APIs. Skip internal helpers.
- **Imports**: stdlib → third-party → local (isort-compatible).
- **Error handling**: Raise specific exceptions. Never `except Exception: pass`.
- **Logging**: Use `logging` module. Never `print()` in production code. `click.echo()` is acceptable only in `jarvis/cli.py`.

### File naming

- Modules: `snake_case.py`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`

### Test files

- Location: `tests/` (mirror the source tree — `tests/core/audio/`, etc.)
- Naming: `test_{module_name}.py`
- Framework: `pytest`
- No test files in production source directories

---

## 6. Latency Rules (CRITICAL)

Latency is the primary product metric. These rules are NON-NEGOTIABLE.

| Rule | Detail |
|------|--------|
| **No blocking in audio path** | `core/audio/` must never call synchronous network I/O or sleep |
| **Streaming TTS first** | TTS must start speaking on first token, not after full response |
| **Intent pre-classifier runs locally** | Simple intents (git, file ops) must NOT hit the LLM API |
| **No cold imports on hot path** | Heavy imports (torch, mlx) must be done at startup, not per-request |
| **Thread affinity** | Audio capture = dedicated thread. LLM calls = thread pool. TTS = dedicated thread |

When adding new features, explicitly document their latency impact in the PR description.

---

## 7. What Agents Must NOT Do

- **Do NOT** add `try/except` blocks that swallow exceptions silently
- **Do NOT** create new top-level files in the project root (use the correct module directory)
- **Do NOT** install new dependencies without checking `requirements.txt` and `pyproject.toml` first
- **Do NOT** add `time.sleep()` in any audio or daemon path
- **Do NOT** commit `.env` files, API keys, or model weights
- **Do NOT** refactor code that is not directly related to the task at hand
- **Do NOT** add features outside the current EPIC scope without user approval
- **Do NOT** run `pip install`, `npm install`, or build commands (user runs those)

---

## 8. Task Execution Protocol

When implementing a task from the roadmap:

1. **Read first** — read the relevant existing files before writing anything
2. **Check scope** — confirm the task belongs to the correct module per §3
3. **Interface before implementation** — define or verify the Protocol in `core/` first
4. **One task = one concern** — do not bundle multiple issues in one implementation
5. **Verify latency impact** — state it explicitly in a comment or PR note
6. **No speculative code** — implement exactly what the issue describes, no extras

---

## 9. SDD Phase Assignments (Agent Teams)

| Phase | Scope in this project |
|-------|-----------------------|
| `sdd-explore` | Read `docs/`, `core/`, `adapters/` — no writes |
| `sdd-propose` | Proposal covers one EPIC at a time |
| `sdd-spec` | One spec per issue (not per EPIC) |
| `sdd-design` | Must include latency impact section |
| `sdd-apply` | Follows scope rules in §3 strictly |
| `sdd-verify` | Cross-checks against `docs/ROADMAP_VOICE_CLI.md` + spec |
| `sdd-archive` | Writes to `docs/` only |

---

## 10. Quick Reference

```
Need to add a new LLM backend?   → adapters/llm/{provider}_adapter.py
Need to add a new TTS engine?    → adapters/tts/{engine}_tts.py
Need to add a new CLI command?   → jarvis/cli.py (thin) + core/ (logic)
Need to add a new tool?          → core/tools/{tool_name}.py (to be created in EPIC 2)
Need to fix audio pipeline?      → core/audio/ — CHECK LATENCY RULES FIRST
Need to update docs?             → docs/ — only if explicitly asked
```

---

*Last updated: 2026-04-06 — aligned with ROADMAP_VOICE_CLI.md (32 issues, 6 EPICs)*
