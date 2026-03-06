from tkinter import Frame
import UI._style_guide as sg
from UI.section_retrieve_data import create_retrieve_data_section
from UI.section_preview_data import create_preview_data_section

def create_data_tab(parent):
    tab = Frame(parent, bg=sg.bg)
    tab.pack(fill="both", expand=True)

    create_retrieve_data_section(tab, 0, 0, 300, 200)
    create_preview_data_section(tab, 0, 2, 500, 200)

    return tab