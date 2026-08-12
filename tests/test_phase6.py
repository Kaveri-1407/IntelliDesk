import json

from core.ml_intent import IntentClassifier
from core.task_planner import TaskPlanner
from core.safety import validate_actions


def test_ml_intent_classification():
    model = IntentClassifier()
    model.train()
    pred, conf = model.predict_with_confidence('open notepad')
    assert pred == 'OPEN_APP'
    assert conf >= 0.0


def test_task_planning_multistep():
    planner = TaskPlanner()
    plan = planner.plan('Open Chrome and search Python tutorials')
    assert plan
    assert any(step.get('action') in {'open_browser', 'open_url'} for step in plan)
    assert any(step.get('action') == 'search_web' for step in plan)


def test_safety_rejects_unsafe_commands():
    unsafe_actions = [
        {'action': 'launch_application', 'name': 'powershell'},
        {'action': 'launch_application', 'name': 'cmd'},
        {'action': 'open_url', 'url': 'https://example.com'},
        {'action': 'create_folder', 'path': 'C:/Windows/System32'}
    ]
    errors = validate_actions(unsafe_actions)
    assert errors


def test_llm_json_plan_is_structured():
    planner = TaskPlanner()
    payload = planner._build_llm_payload('Open Chrome and search Python tutorials')
    assert isinstance(payload, dict)
    assert 'task' in payload
    assert 'actions' in payload
    assert isinstance(payload['actions'], list)
