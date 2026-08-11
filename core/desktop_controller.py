import subprocess
import sys
import webbrowser
from typing import Dict
from . import action_engine


def launch_app(name: str) -> str:
    name = (name or '').lower()
    # allowlist enforced in safety layer; controller safely executes known apps
    try:
        if name in ('notepad', 'notepad.exe'):
            subprocess.Popen(['notepad'])
            return 'Launched Notepad'
        if name in ('calc', 'calculator'):
            subprocess.Popen(['calc'])
            return 'Launched Calculator'
        if name in ('chrome', 'google chrome'):
            if sys.platform.startswith('win'):
                subprocess.Popen('start chrome', shell=True)
            else:
                webbrowser.open('https://www.google.com')
            return 'Launched Chrome'
        if name in ('vscode', 'code', 'visual studio code'):
            try:
                subprocess.Popen(['code'])
            except Exception:
                if sys.platform.startswith('win'):
                    subprocess.Popen('start code', shell=True)
                else:
                    webbrowser.open('https://code.visualstudio.com/')
            return 'Launched VS Code'
        return f'Unknown or disallowed app: {name}'
    except Exception as exc:
        return f'Failed to launch {name}: {exc}'


def focus_app(name: str) -> str:
    # Delegates to action_engine focus_window
    return action_engine.focus_window(name)


def close_app(name: str) -> str:
    return action_engine.close_application(name)


def type_into_active(text: str) -> str:
    return action_engine.type_text(text)


def press_key(key: str) -> str:
    return action_engine.press_key(key)


def send_hotkey(keys) -> str:
    if isinstance(keys, (list, tuple)):
        return action_engine.hotkey(*keys)
    if isinstance(keys, str):
        parts = [k.strip() for k in keys.split('+') if k.strip()]
        return action_engine.hotkey(*parts)
    return 'Invalid hotkey specification'


def take_screenshot(dest_dir: str = None) -> str:
    return action_engine.take_screenshot(dest_dir)
