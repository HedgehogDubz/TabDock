from tkinter import Tk
from UI.custom_widgets import FileListViewer
import UI._style_guide as sg

root = Tk()
root.configure(bg=sg.bg)
root.geometry("600x500")
root.title("File List Viewer Test")

# Create the file list viewer with specific width and height
viewer = FileListViewer(root, directory="Saves/Data", width=500, height=400)
viewer.pack(padx=10, pady=10)

root.mainloop()

