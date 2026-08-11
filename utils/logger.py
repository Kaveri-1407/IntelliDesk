import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'intellidesk.log'

logger = logging.getLogger('intellidesk')
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)

def get_logger():
    return logger
