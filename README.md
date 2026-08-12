# IntelliDesk AI

IntelliDesk AI is an AI-powered desktop automation assistant for Windows.

This project implements Phase 6 of IntelliDesk: an AI/ML-driven automation MVP with natural language intent understanding, structured task planning, safe execution, browser automation, form handling, voice/STT architecture, and GUI integration.

## Project Overview

IntelliDesk acts as an intelligent desktop agent that can:
- Interpret natural language commands using ML and LLM planning
- Classify intent and create structured action plans
- Execute multi-step desktop and browser workflows safely
- Detect and fill non-sensitive web form fields
- Use voice input and optional text-to-speech responses
- Maintain execution history, screenshots, and settings
- Validate all actions through a safety allowlist

## Current Implementation

This repository implements the Phase 6 MVP in full, including:
- AI intent understanding with a local ML classifier and rule-based fallback
- Structured task planning via `core/task_planner.py`
- LLM-based JSON planning fallback in `core/ai_engine.py`
- Multi-step browser and desktop task execution
- Desktop automation primitives and safe action execution
- Browser automation with Playwright in `core/playwright_controller.py`
- Web form detection and safe, non-sensitive form filling
- Voice input architecture in `core/voice_controller.py`
- Optional TTS architecture support in `core/tts_controller.py`
- Task progress and cancel/stop support in `core/action_engine.py`
- History tracking and UI integration
- Screenshot capture and viewer integration
- Settings management and API configuration

## Getting Started

1. Install Python 3.11+.
2. Install dependencies using the provided requirements file:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Install Playwright browsers if you want browser automation:

```powershell
.venv\Scripts\python.exe -m playwright install
```

4. Create a `.env` file in the project root with your OpenAI API key:

```text
OPENAI_API_KEY=sk-...
```

5. Run the application:

```powershell
.venv\Scripts\python.exe app.py
```

## Project Structure

- `app.py` — application entrypoint
- `gui/main_window.py` — Tkinter GUI scaffold
- `core/` — project core modules and automation logic (currently empty)
- `utils/` — helper utilities
- `assets/` — static assets and resources

## Future Enhancements

Planned improvements include:
- natural language understanding with LLMs
- voice recognition and speech synthesis
- task planner and execution engine
- file system and application automation
- memory for user preferences and context
- safety confirmations for destructive commands

## Notes

This repository currently serves as the foundation for building IntelliDesk into a full AI-powered desktop agent. The GUI shell can be expanded with real AI, automation, and user interaction features.

## Implemented (MVP)

- Natural-language command input with OpenAI integration (uses `.env` OPENAI_API_KEY)
- Rule-based fallback parser when the API key is missing or AI parsing fails
- Desktop automation primitives: launch applications, type text, press keys, hotkeys, take screenshots
- Browser helpers: open URLs and Google searches
- Form automation commands (fill/select/check) with manual confirmation requirement
- History persisted to `history.json` (no secrets stored)
- Screenshots viewer and folder access
- Settings page showing API status and automation settings
- Emergency Stop for running automation

## Quick start

1. Create a `.env` file in the project root containing your OpenAI key:

```
OPENAI_API_KEY=sk-...
```

2. Install dependencies and Playwright browsers:

```powershell
python -m pip install -r requirements.txt
python -m playwright install
```

3. Run the app from source:

```powershell
python app.py
```

## Safety

- All AI-produced actions are validated against an allowlist (`core/safety.py`).
- Forbidden keywords like `powershell`, `cmd`, `shutdown` are blocked.
- No automatic arbitrary shell execution or unrestricted PowerShell/CMD execution.
- No destructive system commands, file deletion, or registry edits are allowed.
- Sensitive form fields are never auto-submitted.

## Testing

Run the Phase 6 validation suite using the project virtual environment:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Then verify compilation:

```powershell
.venv\Scripts\python.exe -m compileall core gui utils app.py
```

## Current Limitations

- Browser automation requires Playwright browser runtimes installed.
- Voice/STT depends on available microphone hardware and `speechrecognition` support.
- OpenAI LLM planning requires a valid `.env` `OPENAI_API_KEY`.
- Form automation is safe for ordinary non-sensitive fields only; sensitive fields are blocked.
- The app is an MVP and not production hardened.

## Build artifacts (created during this session)

- Built executable: `dist/app.exe` (IntelliDesk GUI single-file build)
- Inno Setup script: `build/IntelliDesk_installer.iss` (create installer locally with Inno Setup)

## Building the executable

PyInstaller is used to produce a single-file Windows GUI executable. Example commands:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --add-data "screenshots;screenshots" app.py
```

After a successful build the executable is available at `dist/app.exe`.

## Creating the installer

You can use Inno Setup to create an installer from the built exe. Example steps:

1. Install Inno Setup: https://jrsoftware.org/
2. Open `build/IntelliDesk_installer.iss` and ensure the `MyAppExe` preprocessor variable points to the actual built executable path, typically `..\dist\IntelliDesk.exe`.
3. Compile the script in Inno Setup to produce `IntelliDesk_Setup.exe`.

Note: This environment created the script but cannot compile Inno Setup installers here.

***
