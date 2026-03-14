# Product Requirements Document (PRD)

## 1. Meta Information
- **Project Name:** Gemini Voice CLI Extension (Codename: J.A.R.V.I.S.)
- **Status:** Draft
- **Objective:** Build a voice-first intermediary extension for the Gemini CLI that intercepts complex text outputs, summarizes them conversationally, and allows hands-free control (approval/rejection/prompting) via voice commands.

## 2. Problem Statement
Developers using CLI-based LLMs often receive massive walls of text or code blocks. Reading this while trying to focus on another task breaks the flow. Furthermore, standard text-to-speech (TTS) systems reading raw code aloud are practically useless. A conversational, context-aware voice interface is required to act as an intelligent co-pilot.

## 3. Core Features & Requirements

### 3.1. Intelligent Summarization (The "Translator")
- **Req 3.1.1:** The system MUST NOT read raw code blocks aloud.
- **Req 3.1.2:** All Gemini outputs must pass through a secondary "summarization prompt" before hitting the TTS engine. Example: Instead of reading a Python script, the system should say: *"I've generated the Python script using pandas as requested. Should I execute it or save it to a file?"*

### 3.2. Hybrid Voice I/O Engine
- **Req 3.2.1 (STT):** Support for interchangeable Speech-to-Text engines. Must include a Local provider (e.g., Whisper.cpp) and a Remote provider (e.g., OpenAI Whisper API).
- **Req 3.2.2 (TTS):** Support for interchangeable Text-to-Speech engines. Must include a Local provider (e.g., Piper, Coqui) and a Remote provider (e.g., ElevenLabs).
- **Req 3.2.3:** Switching between Local and Remote modes must be possible via environment variables or a configuration file without changing the core business logic.

### 3.3. Barge-in & Interruption
- **Req 3.3.1:** The user MUST be able to interrupt the assistant while it is speaking.
- **Req 3.3.2:** The system requires a low-latency Voice Activity Detection (VAD) module constantly monitoring the microphone line.
- **Req 3.3.3:** Upon detecting user speech, the system must immediately halt the TTS audio stream and transition to the `LISTENING` state.

### 3.4. Workflow Control via Voice
- **Req 3.4.1:** The system must recognize explicit confirmation or rejection intents (e.g., "Yes, run it", "No, cancel", "Explain the second function").
- **Req 3.4.2:** Actions requiring system modifications (writing files, executing shell commands) MUST be paused pending voice approval.

## 4. Out of Scope for v1.0
- Wake-word detection (e.g., saying "Hey Gemini" to wake the CLI up from the background). The CLI will be assumed to be in an active conversational loop when executed.
- Visual UI. This is strictly a CLI/Voice extension.
