from core.playwright_controller import fill_field_by_label, is_available
from pathlib import Path

html = Path(__file__).resolve().parents[0] / 'form_test.html'
url = f'file:///{html.as_posix()}'
print('Playwright available:', is_available())
print('Testing fill Full Name...')
print(fill_field_by_label(url, 'Full Name', 'Kaveri'))
print('Testing fill Email...')
print(fill_field_by_label(url, 'Email Address', 'kaveri@example.com'))
