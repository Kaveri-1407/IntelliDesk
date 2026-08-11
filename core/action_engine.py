import os
import subprocess
import webbrowser
import time
import sys
from pathlib import Path
from typing import Callable, Dict, List
from . import safety
from . import desktop_controller
from . import browser_controller
from . import form_controller
from . import playwright_controller
_pyautogui = None

def _get_pyautogui():
    """Lazy import pyautogui so the app doesn't crash if it's unavailable at import time."""
    global _pyautogui
    if _pyautogui is not None:
        return _pyautogui
    try:
        import pyautogui as pag
        _pyautogui = pag
        return _pyautogui
    except Exception:
        _pyautogui = None
        return None

try:
    import psutil
except Exception:
    psutil = None

try:
    import pygetwindow as gw
except Exception:
    gw = None


def _safe_callback(cb: Callable[[str], None], text: str):
    try:
        if cb:
            cb(text)
    except Exception:
        pass


def launch_application(name: str) -> str:
    name = (name or "").lower()
    try:
        # Allowlist specific application names only for safety.
        if name in ("notepad", "notepad.exe"):
            subprocess.Popen(["notepad"])
            return "Launched Notepad"
        if name in ("calc", "calculator"):
            subprocess.Popen(["calc"])
            return "Launched Calculator"
        if name in ("chrome", "google chrome", "browser", "edge"):
            # Use start to open Chrome on Windows; this is allowlisted only.
            if sys.platform.startswith("win"):
                subprocess.Popen("start chrome", shell=True)
            else:
                webbrowser.open("https://www.google.com")
            return f"Attempted to launch {name}"

        if name in ("vscode", "code", "visual studio code"):
            # Try to launch VS Code via the `code` command on PATH, or use start on Windows
            try:
                subprocess.Popen(["code"])
            except Exception:
                if sys.platform.startswith("win"):
                    subprocess.Popen("start code", shell=True)
                else:
                    webbrowser.open("https://code.visualstudio.com/")
            return "Attempted to launch VS Code"

        return f"Launch not allowed or unknown application: {name}"
    except Exception as exc:
        return f"Failed to launch {name}: {exc}"


def open_url(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Opened URL: {url}"
    except Exception as exc:
        return f"Failed to open URL: {exc}"


def open_folder(path: str) -> str:
    try:
        if not os.path.exists(path):
            return f"Folder does not exist: {path}"
        if sys.platform.startswith("win"):
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
        return f"Opened folder: {path}"
    except Exception as exc:
        return f"Failed to open folder: {exc}"


def create_folder(path: str) -> str:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as exc:
        return f"Failed to create folder: {exc}"


def type_text(text: str) -> str:
    pag = _get_pyautogui()
    if not pag:
        return "pyautogui not available: cannot type text"
    try:
        pag.write(text, interval=0.03)
        return "Typed text"
    except Exception as exc:
        return f"Failed to type text: {exc}"


def press_key(key: str) -> str:
    pag = _get_pyautogui()
    if not pag:
        return "pyautogui not available: cannot press key"
    try:
        pag.press(key)
        return f"Pressed key: {key}"
    except Exception as exc:
        return f"Failed to press key: {exc}"


def hotkey(*keys: str) -> str:
    pag = _get_pyautogui()
    if not pag:
        return "pyautogui not available: cannot send hotkey"
    try:
        pag.hotkey(*keys)
        return f"Sent hotkey: {keys}"
    except Exception as exc:
        return f"Failed to send hotkey: {exc}"


def take_screenshot(save_dir: str = None) -> str:
    pag = _get_pyautogui()
    if not pag:
        return "pyautogui not available: cannot take screenshot"
    try:
        # Save screenshots inside the project `screenshots/` folder by default
        project_root = Path(__file__).resolve().parents[1]
        save_dir = save_dir or os.path.join(project_root, "screenshots")
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        filename = time.strftime("intellidesk_screenshot_%Y%m%d_%H%M%S.png")
        path = os.path.join(save_dir, filename)
        img = pag.screenshot()
        img.save(path)
        return f"Screenshot saved: {path}"
    except Exception as exc:
        return f"Failed to take screenshot: {exc}"


def focus_window(title: str) -> str:
    if not gw:
        return "pygetwindow not available: cannot focus windows"
    try:
        wins = gw.getWindowsWithTitle(title)
        if not wins:
            return f"Window not found: {title}"
        wins[0].activate()
        return f"Focused window: {title}"
    except Exception as exc:
        return f"Failed to focus window: {exc}"


def close_application(name: str) -> str:
    if not psutil:
        return "psutil not available: cannot close applications"
    try:
        # Restrict close-by-name to an allowlist to avoid terminating arbitrary processes.
        allowlist = ["notepad.exe", "calculator.exe", "Calculator.exe", "chrome.exe", "Code.exe"]
        matched = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = (proc.info.get("name") or "")
                if name.lower() in pname.lower() and pname in allowlist:
                    proc.terminate()
                    matched.append(proc.info)
            except Exception:
                pass
        if not matched:
            return f"No running allowed process matched: {name}"
        return f"Requested termination of {len(matched)} allowed process(es) matching: {name}"
    except Exception as exc:
        return f"Failed to close application: {exc}"


def close_active_application() -> str:
    # Close the currently active/focused window safely by sending Alt+F4
    try:
        pag = _get_pyautogui()
        if pag:
            pag.hotkey('alt', 'f4')
            return "Sent Alt+F4 to active window"
        if gw:
            w = gw.getActiveWindow()
            if w:
                w.close()
                return f"Closed active window: {w.title}"
            return "No active window found"
        return "No automation backend available to close active window"
    except Exception as exc:
        return f"Failed to close active application: {exc}"


def execute_actions(actions: List[Dict], feedback: Callable[[str], None] = None):
    """Execute a sequence of action dictionaries.

    The feedback callback is called with status strings and should be safe to call from
    a worker thread (caller may marshal updates to the GUI thread).
    """
    # Validate actions first
    try:
        errs = safety.validate_actions(actions)
        if errs:
            for e in errs:
                _safe_callback(feedback, f"Safety validation error: {e}")
            return
    except Exception as ex:
        _safe_callback(feedback, f"Safety validator failed: {ex}")
        return

    # Execute actions sequentially
    for act in actions:
        if _check_stop():
            _safe_callback(feedback, "Automation stopped by user request.")
            return
        a = act.get("action")
        try:
            if a == "launch_application":
                name = act.get("name")
                res = launch_application(name)
                _safe_callback(feedback, res)
                time.sleep(1)
            elif a == "open_browser":
                browser = act.get("browser")
                res = playwright_controller.open_browser(browser)
                _safe_callback(feedback, res)
            elif a == "open_url":
                url = act.get("url")
                res = playwright_controller.open_url(url)
                _safe_callback(feedback, res)
            elif a == "search_web":
                query = act.get("query")
                res = playwright_controller.search_web(query)
                _safe_callback(feedback, res)
            elif a == "navigate_back":
                res = playwright_controller.navigate_back()
                _safe_callback(feedback, res)
            elif a == "navigate_forward":
                res = playwright_controller.navigate_forward()
                _safe_callback(feedback, res)
            elif a == "reload_page":
                res = playwright_controller.reload_page()
                _safe_callback(feedback, res)
            elif a == "get_page_title":
                res = playwright_controller.get_page_title()
                _safe_callback(feedback, res)
            elif a == "close_browser":
                res = playwright_controller.close_browser()
                _safe_callback(feedback, res)
            elif a == "click_safe_element":
                text = act.get("text") or act.get("field")
                res = form_controller.click_safe_element(text)
                _safe_callback(feedback, res)
            elif a == "fill_safe_field":
                field = act.get("field")
                value = act.get("value")
                res = form_controller.fill_field(field, value)
                _safe_callback(feedback, res)
            elif a == "select_option":
                field = act.get("field")
                value = act.get("value")
                res = form_controller.select_option(field, value)
                _safe_callback(feedback, res)
            elif a == "check_checkbox":
                field = act.get("field")
                res = form_controller.check_checkbox(field)
                _safe_callback(feedback, res)
            elif a == "uncheck_checkbox":
                field = act.get("field")
                res = form_controller.uncheck_checkbox(field)
                _safe_callback(feedback, res)
            elif a == "submit_form":
                res = form_controller.submit_form()
                _safe_callback(feedback, res)
            elif a == "open_folder":
                path = act.get("path")
                res = open_folder(path)
                _safe_callback(feedback, res)
            elif a == "create_folder":
                path = act.get("path")
                res = create_folder(path)
                _safe_callback(feedback, res)
            elif a == "type_text":
                text = act.get("text")
                # small pause to ensure focus
                time.sleep(0.5)
                res = desktop_controller.type_into_active(text)
                _safe_callback(feedback, res)
            elif a == "press_key":
                key = act.get("key") or act.get("k")
                res = desktop_controller.press_key(key)
                _safe_callback(feedback, res)
            elif a == "hotkey":
                keys = act.get("keys") or act.get("k") or []
                if isinstance(keys, str):
                    keys = [k.strip() for k in keys.split("+") if k.strip()]
                res = desktop_controller.send_hotkey(keys)
                _safe_callback(feedback, res)
            elif a == "take_screenshot":
                res = desktop_controller.take_screenshot()
                _safe_callback(feedback, res)
            elif a == 'upload_file':
                field = act.get('field')
                path = act.get('path')
                _safe_callback(feedback, f"Upload action prepared for field '{field}' with path '{path}'. Manual confirmation required.")
            elif a == "close_active_application":
                res = close_active_application()
                _safe_callback(feedback, res)
            elif a == "wait":
                secs = float(act.get("seconds", 1))
                _safe_callback(feedback, f"Waiting {secs} second(s)...")
                time.sleep(secs)
            elif a == "focus_window":
                title = act.get("title") or act.get("name")
                res = focus_window(title)
                _safe_callback(feedback, res)
            elif a == "close_application":
                name = act.get("name")
                res = close_application(name)
                _safe_callback(feedback, res)
            elif a == "unknown":
                _safe_callback(feedback, f"I don't understand the command: {act.get('text')}")
            else:
                _safe_callback(feedback, f"Unhandled action: {a}")
        except Exception as exc:
            _safe_callback(feedback, f"Error executing action {a}: {exc}")


# Automation stop control
_stop_requested = False


def request_stop():
    global _stop_requested
    _stop_requested = True


def clear_stop_request():
    global _stop_requested
    _stop_requested = False


def _check_stop():
    return _stop_requested
