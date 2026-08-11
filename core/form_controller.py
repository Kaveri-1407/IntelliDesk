import os
import json
from typing import List, Dict, Tuple
from pathlib import Path
from . import safety
from . import browser_controller
from core import playwright_controller


"""Form controller: safe integration with Playwright browser automation."""


def detect_fields_from_url(url: str) -> List[Dict]:
    try:
        return playwright_controller.detect_form_fields(url)
    except Exception:
        return []


def fill_field(field_name: str, value: str) -> str:
    return playwright_controller.fill_safe_field(field_name, value)


def select_option(field_name: str, option_value: str) -> str:
    return playwright_controller.select_option(field_name, option_value)


def check_checkbox(field_name: str) -> str:
    return playwright_controller.check_checkbox(field_name)


def uncheck_checkbox(field_name: str) -> str:
    return playwright_controller.uncheck_checkbox(field_name)


def click_safe_element(target: str) -> str:
    return playwright_controller.click_safe_element(target)


def submit_form() -> str:
    return playwright_controller.submit_form()


def review_form_summary(fields: List[Dict]) -> str:
    lines = ['Form review:']
    for f in fields:
        name = f.get('label') or f.get('name') or f.get('id')
        val = f.get('value', '')
        sensitive = ' [sensitive]' if f.get('sensitive') else ''
        lines.append(f"- {name}: {val}{sensitive}")
    return '\n'.join(lines)


def _is_sensitive_url(url: str) -> bool:
    if not url:
        return True
    low = url.lower()
    sensitive = ['payment', 'checkout', 'bank', 'login', 'password', 'otp', 'pay', 'stripe', 'paypal', 'auth', 'account', 'delete', 'tax', 'ssn']
    return any(s in low for s in sensitive)


def detect_fields_from_html(html: str) -> List[Dict]:
    return []


def prepare_fill_actions(fields: List[Dict]) -> List[Dict]:
    return []


def submit_form_simulated(actions: List[Dict]) -> Tuple[bool,str]:
    return False, 'Submission requires explicit user confirmation. Not submitted.'


def upload_file(field_identifier: str, file_path: str) -> Dict:
    return {'action':'upload_file','field':field_identifier,'path':file_path}
