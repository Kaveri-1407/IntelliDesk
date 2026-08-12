import tkinter as tk
from tkinter import ttk
from pathlib import Path
from core.history import load_history, clear_history
from core import action_engine, form_controller, playwright_controller
from utils import config
import os
from tkinter import messagebox
try:
    from PIL import Image, ImageTk
    _pillow_available = True
except Exception:
    Image = None
    ImageTk = None
    _pillow_available = False
import io


def make_sidebar(root, on_select):
    frame = tk.Frame(root, bg='#1b1b1b')
    buttons = [
        ('Home', 'home'),
        ('AI Assistant', 'assistant'),
        ('Automation', 'automation'),
        ('Browser', 'browser'),
        ('Forms', 'forms'),
        ('History', 'history'),
        ('Screenshots', 'screenshots'),
        ('Settings', 'settings'),
        ('About', 'about')
    ]
    for idx, (label, key) in enumerate(buttons):
        b = tk.Button(frame, text=label, fg='white', bg='#2b2b2b', relief='flat', command=lambda k=key: on_select(k))
        b.pack(fill='x', pady=2, padx=6)
    return frame


def history_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='History', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)
    topbar = tk.Frame(f, bg='#1e1e1e')
    tk.Label(topbar, text='Search:', fg='white', bg='#1e1e1e').pack(side='left', padx=6)
    search_entry = tk.Entry(topbar)
    search_entry.pack(side='left', padx=6)
    tk.Button(topbar, text='Go', command=lambda: load(search_entry.get().strip())).pack(side='left', padx=6)
    topbar.pack(anchor='w', padx=10)

    listbox = tk.Listbox(f, bg='#2b2b2b', fg='white', width=100)
    listbox.pack(padx=10, pady=6, fill='both', expand=True)

    displayed_items = []

    def load(query: str = None):
        nonlocal displayed_items
        listbox.delete(0, 'end')
        displayed_items = []
        for e in load_history():
            ts = e.get('timestamp')
            cmd = e.get('command')
            status = e.get('status')
            line = f"{ts} | {status} | {cmd}"
            if query:
                if query.lower() in line.lower():
                    listbox.insert('end', line)
                    displayed_items.append(e)
            else:
                listbox.insert('end', line)
                displayed_items.append(e)

    def clear():
        if messagebox.askyesno('Clear History', 'Clear all history? This action cannot be undone.'):
            clear_history()
            load()

    def view_details():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(displayed_items):
            return
        item = displayed_items[idx]
        detail = tk.Toplevel(f)
        detail.title('History Detail')
        txt = tk.Text(detail, width=100, height=30)
        txt.pack()
        txt.insert('1.0', str(item))
        txt.config(state='disabled')

    btn_frame = tk.Frame(f, bg='#1e1e1e')
    tk.Button(btn_frame, text='Clear History', command=clear).pack(side='left', padx=6)
    btn_frame.pack(anchor='e', pady=6, padx=10)

    load()
    return f


def screenshots_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Screenshots', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    listbox = tk.Listbox(f, bg='#2b2b2b', fg='white')
    listbox.pack(fill='both', expand=True, padx=10, pady=6)

    def load():
        listbox.delete(0, 'end')
        screenshots_dir = Path(config.SCREENSHOT_DIR)
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(screenshots_dir.glob('*.png'), reverse=True)
        for p in files:
            listbox.insert('end', str(p.name))

    def open_selected():
        sel = listbox.curselection()
        if not sel:
            return
        name = listbox.get(sel[0])
        path = os.path.join(config.SCREENSHOT_DIR, name)
        try:
            if _pillow_available:
                img = Image.open(path)
                preview = tk.Toplevel(f)
                preview.title(name)
                preview.geometry('800x600')
                img.thumbnail((780, 560))
                tkimg = ImageTk.PhotoImage(img)
                lbl = tk.Label(preview, image=tkimg)
                lbl.image = tkimg
                lbl.pack()
            else:
                messagebox.showinfo('Preview unavailable', 'Pillow is not installed. Opening screenshot with the default system viewer.')
                os.startfile(path)
        except Exception:
            try:
                os.startfile(path)
            except Exception:
                messagebox.showerror('Error', f'Unable to open screenshot: {name}')

    btns = tk.Frame(f, bg='#1e1e1e')
    tk.Button(btns, text='Refresh', command=load).pack(side='left', padx=6)
    tk.Button(btns, text='Open', command=open_selected).pack(side='left', padx=6)
    tk.Button(btns, text='Open Folder', command=lambda: os.startfile(config.SCREENSHOT_DIR)).pack(side='left', padx=6)
    def delete_selected():
        sel = listbox.curselection()
        if not sel:
            return
        name = listbox.get(sel[0])
        if messagebox.askyesno('Delete', f'Delete screenshot {name}?'):
            try:
                os.remove(os.path.join(config.SCREENSHOT_DIR, name))
                load()
            except Exception:
                messagebox.showerror('Error', f'Unable to delete screenshot: {name}')
    tk.Button(btns, text='Delete', command=delete_selected).pack(side='left', padx=6)
    btns.pack(anchor='e', pady=6, padx=10)

    load()
    return f


def settings_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Settings', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)
    from utils import settings
    s = settings.load_settings()
    status = 'Configured' if config.OPENAI_API_KEY else 'Missing'
    tk.Label(f, text=f'API Status: {status}', fg='white', bg='#1e1e1e', font=('Arial', 12)).pack(anchor='w', padx=10, pady=4)

    voice_var = tk.BooleanVar(value=bool(s.get('voice_assistant', True)))
    tts_var = tk.BooleanVar(value=bool(s.get('voice_response', True)))

    tk.Label(f, text='Model:', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10)
    model_entry = tk.Entry(f)
    model_entry.insert(0, s.get('model'))
    model_entry.pack(anchor='w', padx=10)

    tk.Label(f, text='Automation delay (s):', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10)
    delay_entry = tk.Entry(f)
    delay_entry.insert(0, str(s.get('automation_delay')))
    delay_entry.pack(anchor='w', padx=10)

    tk.Label(f, text='Screenshot folder:', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10)
    ss_entry = tk.Entry(f, width=60)
    ss_entry.insert(0, s.get('screenshot_dir'))
    ss_entry.pack(anchor='w', padx=10)

    tk.Checkbutton(f, text='Voice Assistant: ON', variable=voice_var, bg='#1e1e1e', fg='white', selectcolor='#2a2a2a', activebackground='#1e1e1e', activeforeground='white').pack(anchor='w', padx=10, pady=4)
    tk.Checkbutton(f, text='Voice Response: ON', variable=tts_var, bg='#1e1e1e', fg='white', selectcolor='#2a2a2a', activebackground='#1e1e1e', activeforeground='white').pack(anchor='w', padx=10, pady=4)
    tk.Label(f, text=f'Microphone: {"Available" if __import__("core.voice_controller", fromlist=["DEFAULT_VOICE_CONTROLLER"]).DEFAULT_VOICE_CONTROLLER.is_available() else "Unavailable"}', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10, pady=2)
    tk.Label(f, text='Speech Recognition: Available / Unavailable', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10, pady=2)
    tk.Label(f, text=f'ML Model: {"Loaded" if __import__("core.ml_intent", fromlist=["DEFAULT_INTENT_CLASSIFIER"]).DEFAULT_INTENT_CLASSIFIER.predict_with_confidence("open notepad")[0] else "Not loaded"}', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10, pady=2)
    tk.Label(f, text='LLM: Configured / Missing', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10, pady=2)

    def save():
        new = {
            'model': model_entry.get().strip() or s.get('model'),
            'automation_delay': float(delay_entry.get() or s.get('automation_delay')),
            'screenshot_dir': ss_entry.get().strip() or s.get('screenshot_dir'),
            'safety_mode': s.get('safety_mode'),
            'theme': s.get('theme'),
            'version': s.get('version'),
            'voice_assistant': bool(voice_var.get()),
            'voice_response': bool(tts_var.get()),
        }
        settings.save_settings(new)
        messagebox.showinfo('Settings', 'Settings saved. Restart app to apply certain changes.')

    tk.Button(f, text='Save Settings', command=save).pack(padx=10, pady=10)
    return f


def automation_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Automation', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    status_label = tk.Label(f, text='Idle', fg='white', bg='#1e1e1e')
    status_label.pack(anchor='w', padx=10)

    def stop():
        action_engine.request_stop()
        status_label.config(text='Stop requested')

    tk.Button(f, text='Emergency Stop Automation', fg='white', bg='#aa3333', command=stop).pack(anchor='e', padx=10, pady=10)
    return f


def browser_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Browser Controls', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    browser_entry = tk.Entry(f, width=40)
    browser_entry.insert(0, config.BROWSER_NAME)
    browser_entry.pack(padx=10, pady=(0, 6), anchor='w')

    url_entry = tk.Entry(f, width=80)
    url_entry.pack(padx=10)

    status_label = tk.Label(f, text='Browser state unavailable', fg='white', bg='#1e1e1e')
    status_label.pack(anchor='w', padx=10, pady=6)

    output_box = tk.Text(f, width=90, height=8, bg='#2b2b2b', fg='white', state='disabled')
    output_box.pack(padx=10, pady=6)

    def append_output(text: str):
        output_box.config(state='normal')
        output_box.insert('end', text + '\n')
        output_box.see('end')
        output_box.config(state='disabled')

    def refresh_state():
        state = playwright_controller.get_browser_state()
        status = 'Available' if state.get('available') else 'Unavailable'
        open_state = 'Open' if state.get('open') else 'Closed'
        status_label.config(text=f"Browser: {state.get('browser') or config.BROWSER_NAME} | {status} | {open_state} | URL: {state.get('url') or 'none'}")

    def run_action(fn, *args):
        try:
            result = fn(*args)
            append_output(result)
        except Exception as exc:
            append_output(f'Error: {exc}')
        refresh_state()

    def open_browser():
        browser_name = browser_entry.get().strip() or config.BROWSER_NAME
        run_action(playwright_controller.open_browser, browser_name)

    def close_browser():
        run_action(playwright_controller.close_browser)

    def open_page_url():
        raw_url = url_entry.get().strip()
        if not raw_url:
            append_output('Enter a URL or search query first.')
            return
        if not raw_url.startswith('http'):
            raw_url = 'https://' + raw_url
        run_action(playwright_controller.open_url, raw_url)

    def search_web():
        query = url_entry.get().strip()
        if not query:
            append_output('Enter a search query first.')
            return
        run_action(playwright_controller.search_web, query)

    def navigate_back():
        run_action(playwright_controller.navigate_back)

    def navigate_forward():
        run_action(playwright_controller.navigate_forward)

    def reload_page():
        run_action(playwright_controller.reload_page)

    def get_title():
        run_action(playwright_controller.get_page_title)

    top_buttons = tk.Frame(f, bg='#1e1e1e')
    tk.Button(top_buttons, text='Open Browser', command=open_browser).pack(side='left', padx=4)
    tk.Button(top_buttons, text='Close Browser', command=close_browser).pack(side='left', padx=4)
    tk.Button(top_buttons, text='Open URL', command=open_page_url).pack(side='left', padx=4)
    tk.Button(top_buttons, text='Search Web', command=search_web).pack(side='left', padx=4)
    top_buttons.pack(anchor='w', padx=10, pady=6)

    nav_buttons = tk.Frame(f, bg='#1e1e1e')
    tk.Button(nav_buttons, text='Back', command=navigate_back).pack(side='left', padx=4)
    tk.Button(nav_buttons, text='Forward', command=navigate_forward).pack(side='left', padx=4)
    tk.Button(nav_buttons, text='Reload', command=reload_page).pack(side='left', padx=4)
    tk.Button(nav_buttons, text='Get Title', command=get_title).pack(side='left', padx=4)
    nav_buttons.pack(anchor='w', padx=10, pady=6)

    refresh_state()
    return f


def forms_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Forms Automation', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    tk.Label(f, text='Form automation is available via commands or the controls below.', fg='white', bg='#1e1e1e').pack(padx=10)
    tk.Label(f, text='Submission is never automatic for sensitive forms. Review will be requested.', fg='white', bg='#1e1e1e').pack(padx=10, pady=6)

    url_entry = tk.Entry(f, width=80)
    url_entry.pack(padx=10)

    def append_output(text: str):
        output_box.config(state='normal')
        output_box.insert('end', text + '\n')
        output_box.see('end')
        output_box.config(state='disabled')

    output_box = tk.Text(f, width=90, height=8, bg='#2b2b2b', fg='white', state='disabled')
    output_box.pack(padx=10, pady=6)

    fields_listbox = tk.Listbox(f, width=120, height=8, bg='#2b2b2b', fg='white')
    fields_listbox.pack(padx=10, pady=6)

    def refresh_fields(fields):
        fields_listbox.delete(0, 'end')
        for field in fields:
            label = field.get('label') or field.get('name') or field.get('id') or '<unknown>'
            value = field.get('value', '')
            kind = field.get('type', '')
            sensitive = ' [sensitive]' if field.get('sensitive') else ''
            options = f" options={field.get('options')}" if field.get('options') else ''
            fields_listbox.insert('end', f"{label} ({kind}){sensitive}{options} -> {value}")

    def detect_fields():
        url = url_entry.get().strip()
        if not url:
            append_output('Enter a URL to detect form fields.')
            return
        if not url.startswith('http'):
            url = 'https://' + url
        fields = form_controller.detect_fields_from_url(url)
        if not fields:
            append_output('No form fields detected.')
            return
        refresh_fields(fields)
        append_output(f'Detected {len(fields)} field(s) on the page.')

    field_entry = tk.Entry(f, width=40)
    field_entry.pack(padx=10, pady=(4, 2), anchor='w')
    field_entry.insert(0, 'Field name or label')

    value_entry = tk.Entry(f, width=40)
    value_entry.pack(padx=10, pady=(0, 6), anchor='w')
    value_entry.insert(0, 'Value / option')

    def fill_field():
        field_name = field_entry.get().strip()
        value = value_entry.get().strip()
        if not field_name or not value:
            append_output('Field name and value are required.')
            return
        append_output(form_controller.fill_field(field_name, value))

    def select_field_option():
        field_name = field_entry.get().strip()
        option = value_entry.get().strip()
        if not field_name or not option:
            append_output('Field name and option value are required.')
            return
        append_output(form_controller.select_option(field_name, option))

    def check_field():
        field_name = field_entry.get().strip()
        if not field_name:
            append_output('Checkbox field name is required.')
            return
        append_output(form_controller.check_checkbox(field_name))

    def uncheck_field():
        field_name = field_entry.get().strip()
        if not field_name:
            append_output('Checkbox field name is required.')
            return
        append_output(form_controller.uncheck_checkbox(field_name))

    def submit_form():
        append_output(form_controller.submit_form())

    btn_frame = tk.Frame(f, bg='#1e1e1e')
    tk.Button(btn_frame, text='Detect Fields', command=detect_fields).pack(side='left', padx=4)
    tk.Button(btn_frame, text='Fill Field', command=fill_field).pack(side='left', padx=4)
    tk.Button(btn_frame, text='Select Option', command=select_field_option).pack(side='left', padx=4)
    tk.Button(btn_frame, text='Check', command=check_field).pack(side='left', padx=4)
    tk.Button(btn_frame, text='Uncheck', command=uncheck_field).pack(side='left', padx=4)
    tk.Button(btn_frame, text='Submit Form', command=submit_form).pack(side='left', padx=4)
    btn_frame.pack(anchor='w', padx=10, pady=6)

    return f


def home_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='Home Dashboard', fg='white', bg='#1e1e1e', font=('Arial', 18, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    # Quick stats
    screenshots_dir = Path(config.SCREENSHOT_DIR)
    count = len(list(screenshots_dir.glob('*.png'))) if screenshots_dir.exists() else 0
    tk.Label(f, text=f'Screenshots: {count}', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10)
    tk.Label(f, text=f'API Status: {"Configured" if config.OPENAI_API_KEY else "Missing"}', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10)
    return f


def assistant_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='AI Assistant', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)

    try:
        from core.playwright_controller import is_available as playwright_available
        pw_status = 'Available' if playwright_available() else 'Unavailable'
    except Exception:
        pw_status = 'Unavailable'

    tk.Label(f, text=f'Playwright browser automation: {pw_status}', fg='white', bg='#1e1e1e').pack(anchor='w', padx=10, pady=4)
    tk.Label(f, text='Enter a prompt in the command area to run desktop tasks, browser helpers, and safe automation flows.', fg='white', bg='#1e1e1e', wraplength=760, justify='left').pack(anchor='w', padx=10, pady=6)
    tk.Label(f, text='Sensitive form submission is never automatic; review is required before submitting requests.', fg='white', bg='#1e1e1e', wraplength=760, justify='left').pack(anchor='w', padx=10, pady=4)
    return f


def about_page(parent):
    f = tk.Frame(parent, bg='#1e1e1e')
    hdr = tk.Label(f, text='About IntelliDesk', fg='white', bg='#1e1e1e', font=('Arial', 16, 'bold'))
    hdr.pack(anchor='w', padx=10, pady=8)
    text = ('IntelliDesk AI\nVersion: 0.1\nA safe desktop automation assistant.\nFeatures: AI command parsing, automated desktop/browser actions, form automation (manual confirmation), history, screenshots, settings.')
    tk.Label(f, text=text, fg='white', bg='#1e1e1e', justify='left').pack(padx=10, pady=6)
    return f
