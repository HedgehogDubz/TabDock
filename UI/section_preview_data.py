from tkinter import Frame, Label, StringVar, Listbox
import UI._style_guide as sg
from UI.custom_widgets import SectionContainer, FileListViewer
from pathlib import Path

def create_preview_data_section(tab, row, column, width, height):
    preview_data_frame = SectionContainer(tab, "Preview Data", row, column, width, height)

    # Calculate inner dimensions (accounting for padding and border)
    inner_width = width - 25  # Account for padding and border
    inner_height = height - 50  # Account for title and padding

    file_viewer = FileListViewer(preview_data_frame, directory="Data/Saves", width=inner_width, height=inner_height)
    file_viewer.pack(padx=10, pady=15)
    
def get_csv_files():
    path = Path(__file__).parent.parent / "Data"/ "Saves"
    files = [f.name for f in path.glob("*.csv")]
    return files
