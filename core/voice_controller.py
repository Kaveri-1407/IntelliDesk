import threading
from typing import Callable, Optional

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional dependency
    sr = None


class VoiceController:
    """Thin abstraction around speech recognition with graceful fallbacks."""

    def __init__(self):
        self.recognizer = None
        self.microphone = None
        if sr is not None:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception:
                self.recognizer = None
                self.microphone = None
        self._listening = False
        self._thread = None

    def is_available(self) -> bool:
        return self.recognizer is not None and self.microphone is not None

    def listen(self, timeout: float = 8.0, phrase_time_limit: float = 5.0) -> str:
        if sr is None or self.recognizer is None or self.microphone is None:
            raise RuntimeError('Speech recognition is unavailable on this device.')

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            try:
                text = self.recognizer.recognize_google(audio)
                return (text or '').strip()
            except sr.UnknownValueError:
                return ''
            except sr.RequestError as exc:
                raise RuntimeError(f'Speech recognition service unavailable: {exc}') from exc
        except OSError as exc:
            raise RuntimeError('Microphone is unavailable or permission was denied.') from exc
        except sr.WaitTimeoutError:
            return ''
        except Exception as exc:
            raise RuntimeError(f'Voice capture failed: {exc}') from exc

    def transcribe(self, timeout: float = 8.0, phrase_time_limit: float = 5.0) -> str:
        return self.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)

    def start_listening(self, callback: Optional[Callable[[str, str], None]] = None) -> bool:
        if not self.is_available():
            if callback:
                callback('', 'unavailable')
            return False

        self._listening = True

        def _worker():
            try:
                result = self.listen(timeout=10.0, phrase_time_limit=5.0)
                if callback:
                    if result:
                        callback(result, 'result')
                    else:
                        callback('', 'no_speech')
            except Exception as exc:
                if callback:
                    callback(str(exc), 'error')
            finally:
                self._listening = False

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()
        return True

    def stop_listening(self):
        self._listening = False


DEFAULT_VOICE_CONTROLLER = VoiceController()
