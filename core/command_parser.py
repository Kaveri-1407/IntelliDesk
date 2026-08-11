import re
import os
from typing import List, Dict


def parse_command(text: str) -> List[Dict]:
    """Parse a natural-language command into a list of action dictionaries.

    This is a lightweight rule-based parser for Phase 1/2. Actions are simple
    dicts like {"action": "launch_application", "name": "notepad"}.
    """
    s = text.strip()
    lower = s.lower()
    actions = []
    if not lower:
        return actions

    # Open Notepad and type text
    if "notepad" in lower and "open" in lower or lower.startswith("open notepad"):
        actions.append({"action": "launch_application", "name": "notepad"})
        # look for a typed string: "type ... into notepad" or "type '...'"
        m = re.search(r"type(?: this)?(?: text)?(?:\:)?\s*(?:\"([^\"]+)\"|'([^']+)'|(.+?))(?: into notepad|$)", s, re.IGNORECASE)
        if m:
            text_to_type = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if text_to_type:
                actions.append({"action": "wait", "seconds": 1})
                actions.append({"action": "type_text", "text": text_to_type})
        return actions

    # Calculator
    if "calculator" in lower or ("calc" in lower and "open" in lower):
        actions.append({"action": "launch_application", "name": "calc"})
        return actions

    # Open Google or perform search
    if "google" in lower or "youtube" in lower or "chrome" in lower or "browser" in lower or "edge" in lower:
        if "open google" in lower or "go to google" in lower:
            actions.append({"action": "open_url", "url": "https://www.google.com"})
            return actions
        if "open youtube" in lower or "youtube" in lower:
            actions.append({"action": "open_url", "url": "https://www.youtube.com"})
            return actions
        search_match = re.search(r"(?:search(?: google)? for|search for|find)\s+(.+)", s, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            actions.append({"action": "open_url", "url": "https://www.google.com"})
            actions.append({"action": "search_web", "query": query})
            return actions
        if "open" in lower and "http" in lower:
            url_match = re.search(r"(https?://[^\s]+)", s)
            if url_match:
                actions.append({"action": "open_url", "url": url_match.group(1)})
                return actions
        if "open" in lower and "chrome" in lower:
            actions.append({"action": "open_browser", "browser": "chromium"})
            return actions
        if "open" in lower and "browser" in lower:
            actions.append({"action": "open_browser", "browser": "chromium"})
            return actions
        if "open" in lower and "edge" in lower:
            actions.append({"action": "open_browser", "browser": "chromium"})
            return actions
        if "back" in lower or "go back" in lower:
            actions.append({"action": "navigate_back"})
            return actions
        if "forward" in lower or "go forward" in lower:
            actions.append({"action": "navigate_forward"})
            return actions
        if "reload" in lower or "refresh" in lower:
            actions.append({"action": "reload_page"})
            return actions
        if "title" in lower or "page title" in lower:
            actions.append({"action": "get_page_title"})
            return actions
        if "close browser" in lower or "close tab" in lower or "close the browser" in lower:
            actions.append({"action": "close_browser"})
            return actions
        # generic fallback to opening browser if only browser app intent is present
        actions.append({"action": "open_browser", "browser": "chromium"})
        return actions

    # Open folders
    if "downloads" in lower and ("open" in lower or "folder" in lower):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        actions.append({"action": "open_folder", "path": downloads})
        return actions

    # Create folder named X on Desktop
    m = re.search(r"create a folder named\s+\"?([^\"']+)\"?", s, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, name)
        actions.append({"action": "create_folder", "path": path})
        return actions

    # Take screenshot
    if "screenshot" in lower or "take a screenshot" in lower:
        actions.append({"action": "take_screenshot"})
        return actions

    # Form fill commands: "fill name as Kaveri", "enter email as x@x.com"
    m = re.search(r"(?:fill|enter)\s+([a-zA-Z0-9_\- ]+?)\s+(?:as|with|:)\s*\"?([^\"']+)\"?", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        value = m.group(2).strip()
        actions.append({"action": "fill_safe_field", "field": field, "value": value})
        return actions

    # Select / choose / set options: "select state as CA", "choose gender as female"
    m = re.search(r"(?:select|choose|set)\s+([a-zA-Z0-9_\- ]+?)\s+(?:as|to|:)\s*\"?([^\"']+)\"?", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        option = m.group(2).strip()
        actions.append({"action": "select_option", "field": field, "value": option})
        return actions

    m = re.search(r"^(?:check|tick)\s+(.+)$", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        actions.append({"action": "check_checkbox", "field": field})
        return actions

    m = re.search(r"^(?:uncheck|untick)\s+(.+)$", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        actions.append({"action": "uncheck_checkbox", "field": field})
        return actions

    # Upload file: "upload file resume to upload"
    m = re.search(r"upload file\s+(.+)\s+to\s+(.+)", s, re.IGNORECASE)
    if m:
        file_path = m.group(1).strip()
        field = m.group(2).strip()
        actions.append({"action": "upload_file", "field": field, "path": file_path})
        return actions

    # Form automation fields
    m = re.search(r"(?:select|choose|set)\s+([a-zA-Z0-9_\- ]+)\s+(?:as|to|:)?\s*\"?([^\"']+)\"?", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        option = m.group(2).strip()
        actions.append({"action": "select_option", "field": field, "value": option})
        return actions

    m = re.search(r"^(?:check|tick)\s+(.+)$", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        actions.append({"action": "check_checkbox", "field": field})
        return actions

    m = re.search(r"^(?:uncheck|untick)\s+(.+)$", s, re.IGNORECASE)
    if m:
        field = m.group(1).strip()
        actions.append({"action": "uncheck_checkbox", "field": field})
        return actions

    if re.search(r"\b(submit|send|confirm)\b", lower) and "form" in lower:
        actions.append({"action": "submit_form"})
        return actions

    # Type text into active application: "Type Hello" or "type 'Hello'"
    m = re.search(r"^type\s+(?:\"([^\"]+)\"|'([^']+)'|(.+))$", s, re.IGNORECASE)
    if m:
        text_to_type = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if text_to_type:
            actions.append({"action": "type_text", "text": text_to_type})
            return actions

    # Press a key or hotkey: "press Enter", "press ctrl+c" or "press ctrl+v"
    m = re.search(r"^press\s+(.+)$", s, re.IGNORECASE)
    if m:
        key_phrase = m.group(1).strip()
        # hotkey with + or space-separated
        if "+" in key_phrase or "ctrl" in key_phrase.lower() and "+" in key_phrase:
            parts = [p.strip().lower() for p in re.split(r"\+|\s+", key_phrase) if p.strip()]
            # normalize ctrl/control -> ctrl
            parts = ["ctrl" if p in ("control", "ctl") else p for p in parts]
            actions.append({"action": "hotkey", "keys": parts})
            return actions
        # single key press
        actions.append({"action": "press_key", "key": key_phrase.lower()})
        return actions

    # Fallback: unknown action (caller can decide to show help or ask for clarification)
    actions.append({"action": "unknown", "text": s})
    return actions
