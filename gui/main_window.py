import tkinter as tk

def start_app():

    root = tk.Tk()

    root.title("IntelliDesk AI")
    root.geometry("900x600")

    label = tk.Label(
        root,
        text="Welcome to IntelliDesk AI",
        font=("Arial", 22)
    )

    label.pack(pady=40)

    root.mainloop()