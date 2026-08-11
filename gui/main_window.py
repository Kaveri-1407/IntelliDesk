import tkinter as tk
import threading
from tkinter import ttk

from core.ai_engine import interpret_command
from core.action_engine import execute_actions
from gui.pages import (
    make_sidebar,
    home_page,
    assistant_page,
    automation_page,
    browser_page,
    forms_page,
    history_page,
    screenshots_page,
    settings_page,
    about_page,
)
from core.history import add_entry


def start_app():
    root = tk.Tk()
    root.title("IntelliDesk AI")
    root.geometry("1200x750")
    root.configure(bg="#1e1e1e")

    heading = tk.Label(root, text="🤖 IntelliDesk AI", font=("Arial", 24, "bold"), fg="white", bg="#1e1e1e")
    heading.pack(pady=10)

    subtitle = tk.Label(root, text="Your AI-powered desktop automation assistant", font=("Arial", 12), fg="white", bg="#1e1e1e")
    subtitle.pack()

    container = tk.Frame(root, bg='#1e1e1e')
    container.pack(fill='both', expand=True)

    sidebar = make_sidebar(container, lambda key: switch_page(key))
    sidebar.pack(side='left', fill='y')

    main = tk.Frame(container, bg='#252525')
    main.pack(side='left', fill='both', expand=True)

    # Command area
    label = tk.Label(main, text='What would you like me to do?', font=("Arial", 14), fg='white', bg='#252525')
    label.pack(pady=6)

    prompt_box = tk.Text(main, width=90, height=6, font=("Arial", 12))
    prompt_box.pack(pady=6)

    def show_response(text):
        response_box.config(state=tk.NORMAL)
        response_box.delete("1.0", tk.END)
        response_box.insert(tk.END, text)
        response_box.config(state=tk.DISABLED)

    def append_response(text):
        response_box.config(state=tk.NORMAL)
        response_box.insert(tk.END, text + "\n")
        response_box.see(tk.END)
        response_box.config(state=tk.DISABLED)

    def run_prompt():
        prompt = prompt_box.get("1.0", tk.END).strip()
        print("User Prompt:", prompt)
        if not prompt:
            show_response("Please enter a command.")
            return

        # Show COMMAND and clear previous
        show_response("")

        command_label.config(text=f"COMMAND: {prompt}")
        understanding_label.config(text="UNDERSTANDING: Parsing...")
        actions_label.config(text="ACTIONS: -")
        status_label.config(text="STATUS: Running")

        run_button.config(state=tk.DISABLED)


        try:
            actions, note = interpret_command(prompt)
        except Exception as exc:
            understanding_label.config(text=f"UNDERSTANDING: Error: {exc}")
            status_label.config(text="STATUS: Error")
            run_button.config(state=tk.NORMAL)
            return

        if note:
            understanding_label.config(text=f"UNDERSTANDING: {note}")
            append_response(f"Note: {note}")
        else:
            understanding_label.config(text="UNDERSTANDING: AI parsed command")

        if not actions:
            understanding_label.config(text="UNDERSTANDING: No actions parsed")
            status_label.config(text="STATUS: No actions")
            run_button.config(state=tk.NORMAL)
            return

        # Show parsed actions summary
        summary_lines = [f"Planned action: {a.get('action')} { {k:v for k,v in a.items() if k!='action'} }" for a in actions]
        actions_label.config(text="ACTIONS: " + "; ".join([a.get('action') for a in actions]))
        show_response("\n".join(summary_lines) + "\n\nExecuting...\n")
        # If any action looks like form automation or upload, require review
        form_actions = any(a.get('action') in ('upload_file',) or 'field' in a or 'label' in a for a in actions)
        if form_actions:
            confirmed = {'ok': False}

            def on_confirm():
                confirmed['ok'] = True
                review.destroy()

            def on_cancel():
                confirmed['ok'] = False
                review.destroy()

            review = tk.Toplevel(root)
            review.title('Form Review')
            tk.Label(review, text='Please review the prepared form actions before submission', font=('Arial', 12)).pack(padx=10, pady=6)
            tv = tk.Text(review, width=80, height=12)
            tv.pack(padx=10, pady=6)
            for a in summary_lines:
                tv.insert(tk.END, a + '\n')
            btnf = tk.Frame(review)
            tk.Button(btnf, text='Cancel', command=on_cancel).pack(side='left', padx=6)
            tk.Button(btnf, text='Confirm & Submit', command=on_confirm).pack(side='left', padx=6)
            btnf.pack(pady=6)
            root.wait_window(review)
            if not confirmed['ok']:
                understanding_label.config(text='UNDERSTANDING: User canceled form submission')
                status_label.config(text='STATUS: Canceled')
                run_button.config(state=tk.NORMAL)
                return

        def worker():
            def feedback_cb(msg: str):
                # marshal into the Tkinter main thread
                root.after(0, append_response, msg)
            status = 'completed'
            try:
                # clear any previous stop request
                try:
                    from core.action_engine import clear_stop_request
                    clear_stop_request()
                except Exception:
                    pass
                execute_actions(actions, feedback=feedback_cb)
                root.after(0, append_response, "All actions completed.")
            except Exception as exc:
                status = 'failed'
                root.after(0, append_response, f"Execution error: {exc}")
            finally:
                # save to history (safe fields only)
                try:
                    safe_actions = [{k:v for k,v in a.items() if k not in ('path','url')} for a in actions]
                    add_entry(prompt, safe_actions, 'See responses', status)
                except Exception:
                    pass
                root.after(0, status_label.config, {'text': f'STATUS: {status}'})
                root.after(0, run_button.config, {'state': tk.NORMAL})

        threading.Thread(target=worker, daemon=True).start()

    controls = tk.Frame(main, bg='#252525')
    run_button = tk.Button(controls, text="Run", font=("Arial", 12), width=15, command=run_prompt)
    run_button.pack(side='left', padx=6)
    command_label = tk.Label(controls, text='COMMAND:', fg='white', bg='#252525')
    command_label.pack(side='left', padx=6)
    understanding_label = tk.Label(controls, text='UNDERSTANDING:', fg='white', bg='#252525')
    understanding_label.pack(side='left', padx=6)
    actions_label = tk.Label(controls, text='ACTIONS:', fg='white', bg='#252525')
    actions_label.pack(side='left', padx=6)
    status_label = tk.Label(controls, text='STATUS: Idle', fg='white', bg='#252525')
    status_label.pack(side='left', padx=6)
    controls.pack(pady=10)

    response_box = tk.Text(main, width=90, height=12, font=("Arial", 12), bg="#2e2e2e", fg="white", state=tk.DISABLED)
    response_box.pack(pady=10)

    # Pages area
    pages_frame = tk.Frame(main, bg='#252525')
    pages_frame.pack(fill='both', expand=True)

    current_page = {'key': 'assistant', 'widget': None}

    def switch_page(key):
        if current_page['widget']:
            current_page['widget'].pack_forget()
        page_map = {
            'home': home_page,
            'assistant': assistant_page,
            'automation': automation_page,
            'browser': browser_page,
            'forms': forms_page,
            'history': history_page,
            'screenshots': screenshots_page,
            'settings': settings_page,
            'about': about_page,
        }
        page_fn = page_map.get(key, assistant_page)
        w = page_fn(pages_frame)
        w.pack(fill='both', expand=True)
        current_page['widget'] = w
        current_page['key'] = key

    switch_page('assistant')

    root.mainloop()
   