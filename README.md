# IntelliDesk AI

IntelliDesk AI is an AI-powered desktop automation assistant for Windows.

This repository contains the development source. Use `app.py` to run from source.

Features:
- Natural-language command parsing (OpenAI + rule fallback)
- Desktop automation (Notepad, Calculator, Chrome, VS Code)
- Typing, key presses, hotkeys
- Screenshot capture (saved to `screenshots/`)
- Safety validation and allowlist

Build to Windows executable using PyInstaller (see `build_exe.bat`).
# IntelliDesk

IntelliDesk is an AI-powered desktop assistant designed to automate computer tasks through natural language voice and text commands. It combines intent understanding, task planning, and desktop automation to help users perform actions like opening applications, managing files, and executing multi-step workflows.

## Project Overview

IntelliDesk acts as an intelligent personal computer agent that can:
- Interpret user goals using natural language
- Plan and decompose multi-step tasks into actionable steps
- Execute selected desktop operations safely
- Request user confirmation for sensitive actions
- Provide a foundation for future extensions such as memory, computer vision, and enterprise integrations

## Current Implementation

The current repository includes a lightweight Tkinter GUI shell in `gui/main_window.py` and the application entrypoint in `app.py`. The interface accepts prompt input and is ready to be extended with AI and automation backend logic.

## Getting Started

1. Install Python 3.11+.
2. Run the application:

```bash
python app.py
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
- No automatic shell execution, file deletion, registry edits, or system shutdown.
- Form submissions for sensitive forms are never automated.

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
