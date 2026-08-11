from typing import List, Dict

ALLOWED_ACTIONS = {
    'launch_application', 'type_text', 'press_key', 'hotkey', 'take_screenshot',
    'open_browser', 'open_url', 'search_web', 'navigate_back', 'navigate_forward',
    'reload_page', 'get_page_title', 'close_browser', 'click_safe_element',
    'fill_safe_field', 'select_option', 'check_checkbox', 'uncheck_checkbox',
    'submit_form', 'open_folder', 'create_folder', 'wait', 'focus_window',
    'close_application', 'close_active_application'
}

APP_ALLOWLIST = {'notepad', 'calc', 'calculator', 'chrome', 'edge', 'vscode', 'code'}

FORBIDDEN_KEYWORDS = ['powershell', 'cmd', 'shutdown', 'format', 'rm -rf', 'del ', 'curl ', 'wget ', 'javascript:']
SAFE_URL_SCHEMES = {'http', 'https'}


def _validate_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url or '')
        return parsed.scheme in SAFE_URL_SCHEMES
    except Exception:
        return False


def validate_actions(actions: List[Dict]) -> List[str]:
    """Validate a list of structured actions. Return list of error messages (empty if OK)."""
    errors = []
    for i, act in enumerate(actions):
        a = act.get('action')
        if a not in ALLOWED_ACTIONS:
            errors.append(f"Action not allowed: {a}")
            continue

        if a in {'open_url', 'search_web'}:
            url = act.get('url') or ''
            if a == 'open_url' and not _validate_url(url):
                errors.append(f"Invalid or unsupported URL for action {i}: {url}")
            if a == 'search_web' and not isinstance(act.get('query'), str):
                errors.append(f"Missing search query for action {i}")

        if a in {'open_browser', 'close_browser', 'navigate_back', 'navigate_forward', 'reload_page', 'get_page_title', 'submit_form'}:
            pass

        if a in {'click_safe_element', 'fill_safe_field', 'select_option', 'check_checkbox', 'uncheck_checkbox'}:
            target = (act.get('field') or act.get('text') or '').strip()
            if not target:
                errors.append(f"Missing target field or element for action {i}: {a}")
            if any(keyword in target.lower() for keyword in ('password', 'otp', 'pin', 'cvv', 'card', 'bank', 'account', 'ssn', 'secret', 'token')):
                errors.append(f"Sensitive field or target blocked for action {i}: {target}")

        if a == 'launch_application' or a == 'close_application' or a == 'focus_window':
            name = (act.get('name') or act.get('target') or '').lower()
            if not name:
                errors.append(f"Missing application name for action {i}")
            elif name not in APP_ALLOWLIST:
                errors.append(f"Application not allowlisted: {name}")

        for k, v in act.items():
            if isinstance(v, str):
                low = v.lower()
                for bad in FORBIDDEN_KEYWORDS:
                    if bad in low:
                        errors.append(f"Forbidden keyword in action {i}: {bad}")
    return errors
