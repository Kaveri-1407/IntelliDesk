import json
import openai
from typing import Tuple, List, Dict

from utils.openai_client import get_openai_api_key
from core.command_parser import parse_command as rule_parse


def interpret_command(text: str) -> Tuple[List[Dict], str]:
    """Interpret a natural-language command using OpenAI, falling back to rule-based parser.

    Returns a tuple: (actions_list, note). `note` is empty on successful AI parse,
    otherwise contains a message explaining the fallback or error.
    """
    if not text or not text.strip():
        return [], "Empty command"

    try:
        key = get_openai_api_key()
    except Exception as e:
        # No API key: fallback to rule parser and return a clear note
        return rule_parse(text), f"OPENAI_API_KEY missing: {e}"

    try:
        openai.api_key = key
        system = (
            "You are an assistant that converts a single short natural-language desktop command"
            " into a JSON array of simple action objects."
            " Each action must be a JSON object with an 'action' key and optional additional keys"
            " like 'name', 'text', 'key', 'url', 'path', 'seconds'."
            " Allowed actions: launch_application, close_application, open_url, open_folder,"
            " create_folder, type_text, press_key, hotkey, take_screenshot, wait, focus_window."
            " Return only valid JSON (no surrounding backticks) representing an array of action objects."
        )
        user = f"Command: {text}\n\nRespond with the JSON array of actions."

        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=300,
        )

        content = resp.choices[0].message["content"].strip()
        # Try to parse JSON directly
        try:
            actions = json.loads(content)
            if isinstance(actions, list):
                return actions, ""
        except Exception:
            # Attempt to extract JSON substring
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                substring = content[start:end+1]
                try:
                    actions = json.loads(substring)
                    if isinstance(actions, list):
                        return actions, ""
                except Exception:
                    pass

        # If parsing fails, fallback
        return rule_parse(text), "AI response parse failed — used rule-based fallback"

    except Exception as exc:
        # On any OpenAI error, fallback to rule parser
        return rule_parse(text), f"OpenAI API error: {exc} — used rule-based fallback"
