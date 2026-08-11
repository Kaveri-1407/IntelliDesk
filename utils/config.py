import os
from pathlib import Path
from dotenv import load_dotenv

# Load project .env
project_root = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=str(project_root / '.env'))

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
AUTOMATION_DELAY = float(os.getenv('AUTOMATION_DELAY', '0.5'))
SCREENSHOT_DIR = os.getenv('SCREENSHOT_DIR', str(project_root / 'screenshots'))
BROWSER_NAME = os.getenv('BROWSER_NAME', 'chromium')
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'False').strip().lower() in ('1', 'true', 'yes')


def ensure_directories():
    Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
