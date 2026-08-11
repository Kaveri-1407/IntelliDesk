from core.ai_engine import interpret_command
from core.action_engine import execute_actions

tests = ["Open Notepad", "Open Calculator", "Type Hello IntelliDesk"]

for cmd in tests:
    print("CMD:", cmd)
    actions, note = interpret_command(cmd)
    print("NOTE:", note)
    print("ACTIONS:", actions)

    def fb(msg):
        print("FEEDBACK:", msg)

    if actions:
        execute_actions(actions, feedback=fb)

    print('---')
