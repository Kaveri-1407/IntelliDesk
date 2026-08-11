from core import playwright_controller
import webbrowser


def open_url(url: str) -> str:
    if playwright_controller.is_available():
        return playwright_controller.open_url(url)
    try:
        webbrowser.open(url)
        return f'Opened URL: {url}'
    except Exception as exc:
        return f'Failed to open URL: {exc}'


def search_google(query: str) -> str:
    if playwright_controller.is_available():
        return playwright_controller.search_web(query)
    try:
        q = query.strip().replace(' ', '+')
        url = f'https://www.google.com/search?q={q}'
        webbrowser.open(url)
        return f'Searched Google for: {query}'
    except Exception as exc:
        return f'Failed to search Google: {exc}'
