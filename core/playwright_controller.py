import re
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

from utils import config
from utils.logger import get_logger

try:
    from playwright.sync_api import Error as PlaywrightError, Locator, Page, sync_playwright
    _playwright_available = True
except Exception:
    sync_playwright = None
    PlaywrightError = Exception
    Locator = Any
    Page = Any
    _playwright_available = False

_playwright_instance = None
_browser = None
_context = None
_page = None
_current_browser_name = None

SAFE_URL_SCHEMES = {'http', 'https'}
SENSITIVE_FIELD_KEYWORDS = [
    'password', 'pwd', 'pin', 'otp', 'one time', 'ssn', 'cvv', 'card', 'bank', 'account',
    'security', 'secret', 'authentication', 'token', 'credit', 'debit', 'cvc', 'cvv2'
]
UNSAFE_SUBMIT_KEYWORDS = [
    'buy', 'checkout', 'purchase', 'pay', 'bank', 'transfer', 'donate', 'delete', 'cancel', 'remove'
]
SAFE_BUTTON_KEYWORDS = ['submit', 'send', 'continue', 'next', 'finish', 'search', 'confirm']

logger = get_logger()


def is_available() -> bool:
    return _playwright_available


def _normalize_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise ValueError('URL must be a non-empty string')
    candidate = url.strip()
    if not candidate:
        raise ValueError('URL cannot be empty')
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = 'https://' + candidate
        parsed = urlparse(candidate)
    if parsed.scheme not in SAFE_URL_SCHEMES:
        raise ValueError(f'Unsupported URL scheme: {parsed.scheme}')
    return candidate


def _ensure_playwright() -> Any:
    global _playwright_instance
    if _playwright_instance:
        return _playwright_instance
    if not _playwright_available:
        raise RuntimeError('Playwright not installed')
    _playwright_instance = sync_playwright().start()
    return _playwright_instance


def _browser_type(playwright_obj: Any, browser_name: Optional[str]) -> Any:
    if browser_name and browser_name.lower() in ('firefox',):
        return playwright_obj.firefox
    return playwright_obj.chromium


def _ensure_browser(browser_name: Optional[str] = None, headless: Optional[bool] = None) -> None:
    global _browser, _context, _page, _current_browser_name
    browser_name = browser_name or config.BROWSER_NAME
    headless = config.BROWSER_HEADLESS if headless is None else headless
    playwright_obj = _ensure_playwright()
    if _browser and _current_browser_name == browser_name:
        return
    close_browser()
    browser_type = _browser_type(playwright_obj, browser_name)
    _browser = browser_type.launch(headless=headless)
    _context = _browser.new_context()
    _page = _context.new_page()
    _current_browser_name = browser_name
    logger.info('Opened Playwright browser session: %s', browser_name)


def _get_page() -> Page:
    if _page is None:
        raise RuntimeError('Browser not started')
    return _page


def _find_label_text(locator: Locator) -> str:
    try:
        fid = locator.get_attribute('id') or ''
        if fid:
            label = _page.query_selector(f"label[for='{fid}']")
            if label:
                return (label.inner_text() or '').strip()
        # attempt to locate a containing <label>
        label_element = locator.locator('xpath=ancestor::label').first
        if label_element and label_element.count():
            return (label_element.inner_text() or '').strip()
    except Exception:
        pass
    return ''


def _find_control(field_name: str) -> Optional[Locator]:
    page = _get_page()
    normalized = field_name.strip()
    if not normalized:
        return None
    # Try associated label first
    locator = page.locator(f"label:has-text(\"{normalized}\")")
    if locator.count():
        label = locator.first
        fid = label.get_attribute('for')
        if fid:
            candidate = page.locator(f"#{fid}")
            if candidate.count():
                return candidate.first
        candidate = label.locator('input, textarea, select')
        if candidate.count():
            return candidate.first
    # Search by placeholder, name, id, aria-label
    selectors = [
        f'input[placeholder*="{normalized}"]',
        f'textarea[placeholder*="{normalized}"]',
        f'select[placeholder*="{normalized}"]',
        f'input[name*="{normalized}"]',
        f'textarea[name*="{normalized}"]',
        f'select[name*="{normalized}"]',
        f'input[id*="{normalized}"]',
        f'textarea[id*="{normalized}"]',
        f'select[id*="{normalized}"]',
        f'input[aria-label*="{normalized}"]',
        f'textarea[aria-label*="{normalized}"]',
        f'select[aria-label*="{normalized}"]',
    ]
    for selector in selectors:
        candidate = page.locator(selector)
        if candidate.count():
            return candidate.first
    # Try match by visible label text contained in form controls
    candidate = page.locator(f'input:has-text("{normalized}"), textarea:has-text("{normalized}"), select:has-text("{normalized}")')
    if candidate.count():
        return candidate.first
    return None


def _field_type(locator: Locator) -> str:
    tag = (locator.evaluate('el => el.tagName') or '').lower()
    if tag == 'input':
        return (locator.get_attribute('type') or 'text').lower()
    return tag


def _is_sensitive_label(label: str) -> bool:
    if not label:
        return False
    lowered = label.lower()
    return any(keyword in lowered for keyword in SENSITIVE_FIELD_KEYWORDS)


def open_browser(browser_name: Optional[str] = None, headless: Optional[bool] = None) -> str:
    if not _playwright_available:
        return 'Playwright not installed: install playwright and browser runtime.'
    try:
        _ensure_browser(browser_name, headless)
        return f'Browser started: {browser_name or config.BROWSER_NAME}'
    except Exception as exc:
        logger.error('Failed to open browser: %s', exc)
        return f'Failed to start browser: {exc}'


def open_url(url: str, browser_name: Optional[str] = None, headless: Optional[bool] = None) -> str:
    if not _playwright_available:
        return 'Playwright not installed: install playwright and browser runtime.'
    try:
        target = _normalize_url(url)
        _ensure_browser(browser_name, headless)
        page = _get_page()
        page.goto(target, wait_until='domcontentloaded', timeout=30000)
        logger.info('Opened URL: %s', target)
        return f'Opened URL: {target}'
    except Exception as exc:
        logger.error('Failed open_url: %s', exc)
        return f'Failed to open URL: {exc}'


def search_web(query: str, browser_name: Optional[str] = None, headless: Optional[bool] = None) -> str:
    if not _playwright_available:
        return 'Playwright not installed: install playwright and browser runtime.'
    if not query or not query.strip():
        return 'Search query cannot be empty.'
    search_url = f'https://www.google.com/search?q={query.strip().replace(" ", "+")}'
    return open_url(search_url, browser_name, headless)


def navigate_back() -> str:
    try:
        page = _get_page()
        if not page.go_back():
            return 'No previous page in browser history.'
        return 'Navigated back.'
    except Exception as exc:
        logger.error('navigate_back failed: %s', exc)
        return f'Failed to navigate back: {exc}'


def navigate_forward() -> str:
    try:
        page = _get_page()
        if not page.go_forward():
            return 'No forward page in browser history.'
        return 'Navigated forward.'
    except Exception as exc:
        logger.error('navigate_forward failed: %s', exc)
        return f'Failed to navigate forward: {exc}'


def reload_page() -> str:
    try:
        page = _get_page()
        page.reload(wait_until='domcontentloaded', timeout=30000)
        return 'Page reloaded.'
    except Exception as exc:
        logger.error('reload_page failed: %s', exc)
        return f'Failed to reload page: {exc}'


def get_page_title() -> str:
    try:
        page = _get_page()
        return page.title() or 'Untitled page'
    except Exception as exc:
        logger.error('get_page_title failed: %s', exc)
        return f'Failed to get page title: {exc}'


def get_current_url() -> str:
    try:
        page = _get_page()
        return page.url or ''
    except Exception as exc:
        logger.error('get_current_url failed: %s', exc)
        return ''


def detect_form_fields(url: str) -> List[Dict[str, Any]]:
    if not _playwright_available:
        raise RuntimeError('Playwright not installed')
    target = _normalize_url(url)
    open_url(target)
    page = _get_page()
    fields: List[Dict[str, Any]] = []
    controls = page.query_selector_all('input,textarea,select')
    for ctl in controls:
        try:
            tag = (ctl.evaluate('el => el.tagName') or '').lower()
            field_type = (ctl.get_attribute('type') or '').lower() if tag == 'input' else tag
            label = _find_label_text(ctl) or ctl.get_attribute('placeholder') or ctl.get_attribute('name') or ctl.get_attribute('id') or ''
            label = label.strip()
            if not label:
                label = f'{tag} field'
            value = ctl.get_attribute('value') or ''
            is_sensitive = _is_sensitive_label(label)
            options = []
            if tag == 'select':
                for opt in ctl.query_selector_all('option'):
                    options.append((opt.get_attribute('value') or opt.inner_text() or '').strip())
            fields.append({
                'label': label,
                'name': ctl.get_attribute('name') or '',
                'id': ctl.get_attribute('id') or '',
                'type': field_type or tag,
                'placeholder': ctl.get_attribute('placeholder') or '',
                'value': value,
                'sensitive': is_sensitive,
                'options': options,
            })
        except Exception:
            continue
    return fields


def fill_safe_field(field_name: str, value: str) -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    if _is_sensitive_label(field_name):
        return f'Sensitive field detected: {field_name}. Manual entry is required.'
    try:
        page = _get_page()
        control = _find_control(field_name)
        if not control:
            return f'Could not find field matching: {field_name}'
        field_type = _field_type(control)
        if field_type in ('checkbox', 'radio'):
            return f'Field {field_name} is not a plain text field. Use checkbox or radio controls.'
        if field_type == 'select':
            return f'Field {field_name} is a dropdown. Use select_option instead.'
        control.fill(value)
        logger.info('Filled field %s with value', field_name)
        return f'Filled field: {field_name}'
    except Exception as exc:
        logger.error('fill_safe_field failed: %s', exc)
        return f'Failed to fill field {field_name}: {exc}'


def select_option(field_name: str, option_value: str) -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    if _is_sensitive_label(field_name):
        return f'Sensitive field detected: {field_name}. Manual selection is required.'
    try:
        control = _find_control(field_name)
        if not control:
            return f'Could not find select field matching: {field_name}'
        if _field_type(control) != 'select':
            return f'Field {field_name} is not a dropdown/select.'
        selected = control.select_option(label=option_value)
        if not selected:
            selected = control.select_option(value=option_value)
        if not selected:
            return f'Option not found: {option_value}'
        logger.info('Selected option %s for %s', option_value, field_name)
        return f'Selected option: {option_value} for {field_name}'
    except Exception as exc:
        logger.error('select_option failed: %s', exc)
        return f'Failed to select option {option_value} for {field_name}: {exc}'


def check_checkbox(field_name: str) -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    if _is_sensitive_label(field_name):
        return f'Sensitive checkbox detected: {field_name}. Manual entry is required.'
    try:
        control = _find_control(field_name)
        if not control:
            return f'Could not find checkbox matching: {field_name}'
        if _field_type(control) != 'checkbox':
            return f'Field {field_name} is not a checkbox.'
        control.check()
        logger.info('Checked checkbox %s', field_name)
        return f'Checked checkbox: {field_name}'
    except Exception as exc:
        logger.error('check_checkbox failed: %s', exc)
        return f'Failed to check checkbox {field_name}: {exc}'


def uncheck_checkbox(field_name: str) -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    if _is_sensitive_label(field_name):
        return f'Sensitive checkbox detected: {field_name}. Manual entry is required.'
    try:
        control = _find_control(field_name)
        if not control:
            return f'Could not find checkbox matching: {field_name}'
        if _field_type(control) != 'checkbox':
            return f'Field {field_name} is not a checkbox.'
        control.uncheck()
        logger.info('Unchecked checkbox %s', field_name)
        return f'Unchecked checkbox: {field_name}'
    except Exception as exc:
        logger.error('uncheck_checkbox failed: %s', exc)
        return f'Failed to uncheck checkbox {field_name}: {exc}'


def click_safe_element(text: str) -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    try:
        page = _get_page()
        if not text or not text.strip():
            return 'Click target text is required.'
        normalized = text.strip().lower()
        if any(keyword in normalized for keyword in UNSAFE_SUBMIT_KEYWORDS):
            return f'Unsafe click target detected: {text}'
        locator = page.get_by_role('button', name=re.compile(re.escape(text), re.IGNORECASE))
        if locator.count():
            locator.first.click()
            return f'Clicked safe element: {text}'
        locator = page.locator(f'text="{text}"')
        if locator.count():
            locator.first.click()
            return f'Clicked safe element: {text}'
        return f'Could not find clickable element matching: {text}'
    except Exception as exc:
        logger.error('click_safe_element failed: %s', exc)
        return f'Failed to click element {text}: {exc}'


def submit_form() -> str:
    if not _playwright_available:
        return 'Playwright not installed.'
    try:
        page = _get_page()
        candidates = page.query_selector_all('input[type="submit"], button[type="submit"], button:has-text("Submit"), button:has-text("Send"), button:has-text("Confirm")')
        for candidate in candidates:
            label = (candidate.inner_text() or '').strip().lower()
            if any(keyword in label for keyword in UNSAFE_SUBMIT_KEYWORDS):
                continue
            candidate.click()
            return 'Form submit button clicked.'
        return 'No safe submit button found on the page.'
    except Exception as exc:
        logger.error('submit_form failed: %s', exc)
        return f'Failed to submit form: {exc}'


def get_browser_state() -> Dict[str, Any]:
    return {
        'available': _playwright_available,
        'open': _browser is not None,
        'browser': _current_browser_name,
        'url': _page.url if _page is not None else '',
        'title': _page.title() if _page is not None else '',
    }


def close_browser() -> str:
    global _playwright_instance, _browser, _context, _page, _current_browser_name
    if not _browser and not _playwright_instance:
        return 'Browser is not running.'
    try:
        if _page:
            _page.close()
        if _context:
            _context.close()
        if _browser:
            _browser.close()
        if _playwright_instance:
            _playwright_instance.stop()
        _browser = None
        _context = None
        _page = None
        _current_browser_name = None
        _playwright_instance = None
        logger.info('Browser session closed.')
        return 'Browser closed.'
    except Exception as exc:
        logger.error('close_browser failed: %s', exc)
        return f'Failed to close browser: {exc}'
