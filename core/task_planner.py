import json
import re
from typing import Any, Dict, List

from .command_parser import parse_command
from .ml_intent import IntentClassifier
from . import safety


class TaskPlanner:
    """Converts user commands into a safe ordered action list."""

    def __init__(self):
        self.classifier = IntentClassifier()

    def plan(self, command: str) -> List[Dict[str, Any]]:
        text = (command or '').strip()
        if not text:
            return []

        lower = text.lower()
        if 'open' in lower and 'search' in lower and ('chrome' in lower or 'browser' in lower or 'edge' in lower):
            return self._build_multi_step_plan(text)

        intent, confidence = self.classifier.predict_with_confidence(text)
        actions = self._plan_for_intent(text, intent, confidence)
        if actions:
            errors = safety.validate_actions(actions)
            if errors:
                return parse_command(text)
            return actions

        actions = parse_command(text)
        if actions:
            return actions
        return [{"action": "unknown", "text": text}]

    def _plan_for_intent(self, text: str, intent: str, confidence: float) -> List[Dict[str, Any]]:
        lower = text.lower()

        if intent == 'MULTI_STEP_TASK':
            return self._build_multi_step_plan(text)
        if intent == 'OPEN_APP':
            return self._build_open_app_plan(text)
        if intent == 'TYPE_TEXT':
            match = re.search(r"(?:type|write|enter)\s+(?:\"([^\"]+)\"|'([^']+)'|(.+))", text, re.IGNORECASE)
            payload = match.group(1) or match.group(2) or match.group(3) or 'sample text'
            return [{"action": "type_text", "text": payload.strip()}]
        if intent == 'PRESS_KEY':
            key = 'enter'
            if 'escape' in lower:
                key = 'escape'
            elif 'tab' in lower:
                key = 'tab'
            return [{"action": "press_key", "key": key}]
        if intent == 'TAKE_SCREENSHOT':
            return [{"action": "take_screenshot"}]
        if intent == 'SEARCH_WEB':
            query_match = re.search(r"(?:search(?: google)? for|search for|find|lookup)\s+(.+)", text, re.IGNORECASE)
            query = (query_match.group(1) if query_match else text).strip()
            return [{"action": "open_browser", "browser": "chromium"}, {"action": "search_web", "query": query}]
        if intent == 'FORM_FILL':
            field_match = re.search(r"(?:fill|enter)\s+([a-zA-Z0-9_ -]+?)\s+(?:as|with|:)?\s*(?:\"([^\"]+)\"|'([^']+)'|(.+))", text, re.IGNORECASE)
            if field_match:
                field = field_match.group(1).strip() or 'field'
                value = field_match.group(2) or field_match.group(3) or field_match.group(4) or 'sample value'
                return [{"action": "fill_safe_field", "field": field, "value": value.strip()}]
            return [{"action": "fill_safe_field", "field": "name", "value": "sample value"}]
        return []

    def _build_open_app_plan(self, text: str) -> List[Dict[str, Any]]:
        lower = text.lower()
        if 'notepad' in lower:
            return [{"action": "launch_application", "name": "notepad"}]
        if 'calculator' in lower or 'calc' in lower:
            return [{"action": "launch_application", "name": "calc"}]
        if 'chrome' in lower or 'browser' in lower or 'edge' in lower:
            return [{"action": "open_browser", "browser": "chromium"}]
        if 'vscode' in lower or 'code' in lower:
            return [{"action": "launch_application", "name": "code"}]
        return [{"action": "launch_application", "name": "notepad"}]

    def _build_multi_step_plan(self, text: str) -> List[Dict[str, Any]]:
        lower = text.lower()
        actions: List[Dict[str, Any]] = []
        if 'chrome' in lower or 'browser' in lower or 'edge' in lower:
            actions.append({"action": "open_browser", "browser": "chromium"})
            actions.append({"action": "wait", "seconds": 1})
        query_match = re.search(r"(?:search(?: google)? for|search for|find|lookup)\s+(.+)", text, re.IGNORECASE)
        query = query_match.group(1).strip() if query_match else 'python tutorials'
        if 'search' in lower or 'google' in lower or 'find' in lower or 'tutorial' in lower:
            actions.append({"action": "search_web", "query": query})
        elif 'open' in lower and ('chrome' in lower or 'browser' in lower):
            actions.append({"action": "open_url", "url": "https://www.google.com"})
        if 'screenshot' in lower or 'capture' in lower:
            actions.append({"action": "wait", "seconds": 1})
            actions.append({"action": "take_screenshot"})
        return actions or parse_command(text)

    def _build_llm_payload(self, command: str) -> Dict[str, Any]:
        actions = self.plan(command)
        structured = []
        for action in actions:
            item = {"type": action.get("action")}
            for key, value in action.items():
                if key != 'action':
                    item[key] = value
            structured.append(item)
        task_name = 'multi_step' if len(actions) > 1 else 'single_action'
        return {'task': task_name, 'actions': structured}

    def validate_plan(self, plan: List[Dict[str, Any]]) -> List[str]:
        return safety.validate_actions(plan)


DEFAULT_TASK_PLANNER = TaskPlanner()
