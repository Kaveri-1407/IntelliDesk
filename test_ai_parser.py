from core.ai_engine import interpret_command

tests = ["Open Notepad", "Open Calculator"]

for cmd in tests:
    actions, note = interpret_command(cmd)
    print("CMD:", cmd)
    print("NOTE:", note)
    print("ACTIONS:", actions)
    print('---')
