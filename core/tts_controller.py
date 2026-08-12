import threading

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None


class TTSController:
    """Optional text-to-speech wrapper used when the platform supports it."""

    def __init__(self):
        self.engine = None
        if pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
            except Exception:
                self.engine = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return self.engine is not None

    def speak(self, text: str) -> bool:
        if not text or not text.strip() or self.engine is None:
            return False
        try:
            with self._lock:
                self.engine.say(text.strip())
                self.engine.runAndWait()
            return True
        except Exception:
            return False

    def stop_speaking(self):
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass


DEFAULT_TTS_CONTROLLER = TTSController()
