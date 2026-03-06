from tkinter import Tk, Frame, ttk
import UI._style_guide  as sg
from UI.tab_data import create_data_tab

def create_root():
    root = Tk()
    root.geometry("800x600")
    root.title("HedgehogFund")
    root.config(bg="#000000")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background="#000000", borderwidth=0)
    style.configure("TNotebook.Tab", background="#000000", padding=(14, 6))

    style.layout("TNotebook", [
        ("TNotebook.client", {"sticky": "nswe"})  
    ])
    style.map(
        "TNotebook.Tab",
        padding=[
            ("selected", (14, 6)), 
            ("active", (14, 6)), 
            ("!active", (14, 6))
            ],
        background=[
            ("selected", sg.bg), 
            ("active", sg.out_active), 
            ("!active", sg.out_inactive)
            ],
        foreground=[
            ("selected", sg.fg), 
            ("active", sg.fg), 
            ("!active", sg.fg)
            ],
        
        borderwidth=[("selected", 0), ("active", 0)]
    )

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    data_tab = Frame(notebook, bg=sg.bg)
    create_tab = Frame(notebook, bg=sg.bg)
    test_tab = Frame(notebook, bg=sg.bg)

    notebook.add(data_tab, text="Data")
    notebook.add(create_tab, text="Create")
    notebook.add(test_tab, text="Test")

    create_data_tab(data_tab)

    # Force immediate update when switching tabs
    def on_tab_change(event):
        notebook.update_idletasks()

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    root.mainloop()