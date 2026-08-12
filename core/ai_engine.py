import json
from typing import Tuple, List, Dict, Optional

from utils.openai_client import get_openai_api_key
from core.command_parser import parse_command as rule_parse
from core.ml_intent import IntentClassifier
from core.task_planner import TaskPlanner
from core import safety


def classify_intent(text: str) -> Tuple[str, float]:
    classifier = IntentClassifier()
    classifier.train()
    return classifier.predict_with_confidence(text or '')


def _normalize_llm_actions(raw_actions):
    if isinstance(raw_actions, dict):
        raw_actions = raw_actions.get('actions', [])
    if not isinstance(raw_actions, list):
        return []

    normalized = []
    for item in raw_actions:
        if not isinstance(item, dict):
            continue
        action = item.get('type') or item.get('action')
        if not action:
            continue
        record = {'action': action}
        for key, value in item.items():
            if key not in {'type', 'action'}:
                record[key] = value
        normalized.append(record)
    return normalized


def _llm_plan(text: str) -> Optional[List[Dict]]:
    try:
        key = get_openai_api_key()
    except Exception:
        return None

    try:
        import openai
        openai.api_key = key
                
        system = (
            'You are an assistant that converts a single desktop command into structured JSON only. '
            'Return a JSON object with keys: task and actions. Each action must be an object with a "type" field and optional fields: name, text, key, url, query, path, seconds, field, value. '
            'Allowed action types: launch_application, open_browser, open_url, search_web, type_text, press_key, hotkey, take_screenshot, wait, close_application, focus_window, fill_safe_field, submit_form, close_browser. '
            'Do not output any commentary outside the JSON object.'
        )
        user = f'Command: {text}\n\nRespond with JSON only.'

        if hasattr(openai, 'ChatCompletion'):
            resp = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                temperature=0.0,
                max_tokens=300,
            )
            content = resp.choices[0].message['content'].strip()
        else:
            resp = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                temperature=0.0,
                max_tokens=300,
            )
            content = resp.choices[0].message.content.strip()

        parsed = json.loads(content)
        actions = _normalize_llm_actions(parsed)
        if actions:
            return actions
        return None
    except Exception:
        return None


def interpret_command(text: str) -> Tuple[List[Dict], str]:
    """Interpret natural language using the ML model and a safe planner. Fall back to the rule parser when necessary."""
    if not text or not text.strip():
        return [], 'Empty command'

    intent, confidence = classify_intent(text)
    planner = TaskPlanner()
    plan = planner.plan(text)

    if plan and plan != [{'action': 'unknown', 'text': text}]:
        errors = safety.validate_actions(plan)
        if not errors:
            note = f'AI intent: {intent} ({confidence:.2f})' if intent != 'UNKNOWN' else 'AI intent classification used fallback parser'
            if len(plan) > 1:
                note += ' — multi-step plan created'
            return plan, note

    llm_plan = _llm_plan(text)
    if llm_plan:
        errors = safety.validate_actions(llm_plan)
        if not errors:
            return llm_plan, f'LLM structured plan accepted ({intent})'

    fallback = rule_parse(text)
    if fallback:
        return fallback, f'Used safe fallback parser because the AI plan was unavailable or rejected (intent={intent}, confidence={confidence:.2f})'
    return [], 'No valid action could be parsed from the command.'
