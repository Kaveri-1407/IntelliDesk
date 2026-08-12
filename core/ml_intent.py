import json
import pickle
from pathlib import Path
from typing import Tuple, Optional


INTENT_DATASET = {
    'OPEN_APP': [
        'open notepad', 'launch calculator', 'start chrome', 'open vscode', 'open chrome',
        'launch notepad', 'open calculator', 'start notepad', 'launch chrome', 'open edge'
    ],
    'TYPE_TEXT': [
        'type hello world', 'write hello', 'enter this text', 'type my message',
        'write welcome', 'enter test text', 'type hello intellidesk'
    ],
    'PRESS_KEY': [
        'press enter', 'press escape', 'press tab', 'hit enter', 'press ctrl c',
        'press shift tab', 'press the enter key'
    ],
    'TAKE_SCREENSHOT': [
        'take a screenshot', 'capture the screen', 'screenshot the desktop', 'take screenshot'
    ],
    'SEARCH_WEB': [
        'search google for python', 'find machine learning tutorials', 'search web for tutorials',
        'google python', 'look up open source projects'
    ],
    'FORM_FILL': [
        'fill the registration form', 'fill name as john', 'enter email as test@example.com',
        'complete the contact form', 'fill the sign up form'
    ],
    'MULTI_STEP_TASK': [
        'open chrome and search python tutorials', 'open notepad and type hello',
        'search for python and take a screenshot', 'open browser and find tutorials'
    ],
    'UNKNOWN': [
        'hello', 'what time is it', 'tell me a joke', 'how are you'
    ],
}


class IntentClassifier:
    """Lightweight local intent classifier with a safe fallback to deterministic rules."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else Path(__file__).resolve().parents[1] / 'ml_intent_model.pkl'
        self.vectorizer = None
        self.classifier = None
        self._fallback_loaded = False
        self._last_intent = 'UNKNOWN'
        self._last_confidence = 0.0

    def train(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
        except Exception:
            self._fallback_loaded = True
            return self

        texts = []
        labels = []
        for label, examples in INTENT_DATASET.items():
            for example in examples:
                texts.append(example)
                labels.append(label)

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        X = vectorizer.fit_transform(texts)
        model = LogisticRegression(max_iter=1000)
        model.fit(X, labels)

        self.vectorizer = vectorizer
        self.classifier = model
        self._fallback_loaded = False
        return self

    def load_model(self, path: Optional[str] = None):
        target = Path(path) if path else self.model_path
        if not target.exists():
            self.train()
            return False
        try:
            with open(target, 'rb') as fh:
                payload = pickle.load(fh)
            self.vectorizer = payload.get('vectorizer')
            self.classifier = payload.get('classifier')
            self._fallback_loaded = False
            return True
        except Exception:
            self.train()
            return False

    def save_model(self, path: Optional[str] = None):
        target = Path(path) if path else self.model_path
        if self.vectorizer is None or self.classifier is None:
            self.train()
        if self.vectorizer is None or self.classifier is None:
            return False
        try:
            payload = {'vectorizer': self.vectorizer, 'classifier': self.classifier}
            with open(target, 'wb') as fh:
                pickle.dump(payload, fh)
            return True
        except Exception:
            return False

    def predict(self, text: str) -> str:
        intent, _ = self.predict_with_confidence(text)
        return intent

    def predict_with_confidence(self, text: str) -> Tuple[str, float]:
        if not text or not text.strip():
            return 'UNKNOWN', 0.0

        normalized = text.strip().lower()
        if self.vectorizer is not None and self.classifier is not None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                # Ensure the model is trained on the same vectorizer contract.
                if not hasattr(self.vectorizer, 'transform'):
                    raise ValueError('Vectorizer unavailable')
                features = self.vectorizer.transform([normalized])
                prediction = self.classifier.predict(features)[0]
                probabilities = self.classifier.predict_proba(features)[0]
                confidence = float(max(probabilities)) if probabilities.size else 0.0
                self._last_intent = prediction
                self._last_confidence = confidence
                return prediction, confidence
            except Exception:
                pass

        intent = self._fallback_predict(normalized)
        confidence = self._fallback_confidence(normalized, intent)
        self._last_intent = intent
        self._last_confidence = confidence
        return intent, confidence

    def _fallback_predict(self, text: str) -> str:
        if not text:
            return 'UNKNOWN'

        if any(token in text for token in ('notepad', 'calculator', 'chrome', 'vscode', 'edge', 'browser', 'app')):
            if 'screenshot' in text or 'screen' in text:
                return 'TAKE_SCREENSHOT'
            if 'type' in text or 'write' in text or 'enter' in text:
                if 'open' in text and ('notepad' in text or 'chrome' in text):
                    return 'MULTI_STEP_TASK'
                return 'TYPE_TEXT'
            return 'OPEN_APP'

        if 'press' in text or 'key' in text:
            return 'PRESS_KEY'
        if 'search' in text or 'google' in text or 'find' in text or 'lookup' in text:
            if 'open' in text and ('chrome' in text or 'browser' in text):
                return 'MULTI_STEP_TASK'
            return 'SEARCH_WEB'
        if 'screenshot' in text or 'capture' in text:
            return 'TAKE_SCREENSHOT'
        if 'form' in text or 'fill' in text or 'email' in text or 'registration' in text:
            return 'FORM_FILL'
        if 'and' in text and ('search' in text or 'open' in text):
            return 'MULTI_STEP_TASK'
        return 'UNKNOWN'

    def _fallback_confidence(self, text: str, intent: str) -> float:
        if intent == 'UNKNOWN':
            return 0.15
        if any(token in text for token in ('notepad', 'calculator', 'chrome', 'vscode', 'edge')):
            return 0.9
        if any(token in text for token in ('search', 'google', 'find', 'tutorial')):
            return 0.88
        if any(token in text for token in ('screenshot', 'capture')):
            return 0.92
        if 'form' in text or 'fill' in text:
            return 0.85
        if 'type' in text or 'write' in text:
            return 0.82
        if 'press' in text or 'key' in text:
            return 0.8
        return 0.7

    def as_dict(self):
        return {
            'intent': self._last_intent,
            'confidence': self._last_confidence,
            'model_path': str(self.model_path),
        }


DEFAULT_INTENT_CLASSIFIER = IntentClassifier()
