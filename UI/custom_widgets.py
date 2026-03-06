from tkinter import Entry, Radiobutton, ttk, Frame, Label, Canvas
import UI._style_guide as sg
import os


def StyledEntry(parent, width=10, height=None, **kwargs):
    
    entry = Entry(
        parent,
        width=width,
        font=sg.font_text,
        bg=sg.bg_entry,
        fg=sg.fg,
        insertbackground=sg.fg,
        relief="solid",
        bd=1,
        highlightthickness=0,
        **kwargs
    )

    if height is not None:
        entry._custom_height = height

    return entry


def StyledRadiobutton(parent, text, variable, value, **kwargs):
    """Create a styled Radiobutton widget matching the app theme"""
    radio = Radiobutton(
        parent,
        text=text,
        variable=variable,
        value=value,
        bg=sg.bg,
        fg=sg.fg,
        selectcolor=sg.bg_entry,
        activebackground=sg.bg_entry,
        activeforeground=sg.fg,
        relief="flat",
        bd=0,
        highlightthickness=0,
        indicatoron=False,
        padx=8,
        pady=3,
        font=sg.font_text,
        **kwargs
    )
    return radio


class ToggleButtons(Frame):

    def __init__(self, parent, option1, option2, variable, default=None, **kwargs):
        super().__init__(parent, bg=sg.bg, **kwargs)

        self.variable = variable
        self.option1 = option1
        self.option2 = option2

        if default:
            self.variable.set(default)
        elif not self.variable.get():
            self.variable.set(option1)

        from tkinter import Label

        self.btn1 = Label(
            self,
            text=option1,
            fg=sg.fg,
            font=sg.font_text,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.btn1.pack(side="left", padx=0)

        self.btn2 = Label(
            self,
            text=option2,
            fg=sg.fg,
            font=sg.font_text,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.btn2.pack(side="left", padx=0)

        self.btn1.bind("<Button-1>", lambda e: self._on_click(self.option1))
        self.btn2.bind("<Button-1>", lambda e: self._on_click(self.option2))

        self.variable.trace_add("write", lambda *args: self._update_appearance())

        self._update_appearance()

    def _on_click(self, value):
        current = self.variable.get()
        if current == self.option1:
            self.variable.set(self.option2)
        else:
            self.variable.set(self.option1)

    def _update_appearance(self):
        current = self.variable.get()

        if current == self.option1:
            self.btn1.config(bg=sg.bg_entry)  
        else:
            self.btn1.config(bg=sg.bg_light)  
        
        if current == self.option2:
            self.btn2.config(bg=sg.bg_entry)  
        else:
            self.btn2.config(bg=sg.bg_light)  


def StyledCombobox(parent, values, width=10, height=None, **kwargs):

    style = ttk.Style()

    style.element_options('Combobox.field')

    
    style.configure('Borderless.TCombobox',
                    fieldbackground=sg.bg_entry,
                    background=sg.bg_entry,
                    foreground=sg.fg,
                    arrowcolor=sg.fg,
                    bordercolor=sg.bg_entry,
                    lightcolor=sg.bg_entry,
                    darkcolor=sg.bg_entry,
                    borderwidth=0,
                    relief="flat",
                    padding=(2, 0, 2, 0))  

    style.map('Borderless.TCombobox',
              fieldbackground=[('readonly', sg.bg_entry)],
              background=[('readonly', sg.bg_entry)],
              foreground=[('readonly', sg.fg)],
              bordercolor=[('readonly', sg.bg_entry)],
              lightcolor=[('readonly', sg.bg_entry)],
              darkcolor=[('readonly', sg.bg_entry)])

    combo = ttk.Combobox(
        parent,
        values=values,
        state="readonly",
        font=sg.font_text,
        width=width,
        height=5,  
        style='Borderless.TCombobox',
        **kwargs
    )

    return combo


class SegmentedEntry(Frame):

    def __init__(self, parent, num_chars=4, **kwargs):
        super().__init__(parent, bg=sg.bg, **kwargs)

        self.num_chars = num_chars
        self.entries = []
        self.blink_jobs = []

        for i in range(num_chars):
            entry = Entry(
                self,
                width=1,
                font=sg.font_text,
                bg=sg.bg_entry,
                fg=sg.fg,
                insertbackground=sg.bg_entry,
                relief="solid",
                bd=0,
                highlightthickness=0,
                justify="center",
                insertwidth=0,
                insertofftime=0,
                insertontime=0
            )
            entry.pack(side="left", padx=(0 if i == 0 else 1, 0), ipady=3)
            self.entries.append(entry)

            # Validation to limit to 1 capital letter
            def validate_char(new_text):
                if len(new_text) == 0:
                    return True
                if len(new_text) == 1 and new_text.isalpha():
                    return True
                return False

            validate_cmd = self.register(validate_char)
            entry.config(validate="key", validatecommand=(validate_cmd, '%P'))

            entry.bind('<Key>', lambda e, idx=i: self._on_key_press(e, idx))
            entry.bind('<Left>', lambda e, idx=i: self._on_left_arrow(e, idx))
            entry.bind('<Right>', lambda e, idx=i: self._on_right_arrow(e, idx))
            entry.bind('<BackSpace>', lambda e, idx=i: self._on_backspace(e, idx))
            entry.bind('<FocusIn>', lambda e, idx=i: self._on_focus_in(e, idx))
            entry.bind('<FocusOut>', lambda e, idx=i: self._on_focus_out(e, idx))
            entry.bind('<Button-1>', lambda e, idx=i: self._on_click(e, idx))

    def _on_key_press(self, event, index):
        entry = self.entries[index]

        # Only handle alphabetic characters
        if event.char and event.char.isalpha():
            # Convert to uppercase
            char = event.char.upper()

            # If entry already has a character (bordered), replace it
            if len(entry.get()) > 0:
                entry.delete(0, 'end')
                entry.insert(0, char)
                return 'break'  # Prevent default behavior
            else:
                # If empty, insert the uppercase character
                entry.delete(0, 'end')
                entry.insert(0, char)
                # Advance to next box if not the last one
                if index < self.num_chars - 1:
                    self.after(1, lambda: self._advance_to_next(index))
                return 'break'  # Prevent default behavior

        # Block non-alphabetic characters
        if event.char and event.char.isprintable():
            return 'break'

    def _advance_to_next(self, index):
        if index < self.num_chars - 1:
            self.entries[index + 1].focus_set()
            self.entries[index + 1].icursor(0)

    def _on_left_arrow(self, event, index):
        if index > 0:
            self.entries[index - 1].focus_set()
            self.entries[index - 1].icursor('end')
        return 'break' 

    def _on_right_arrow(self, event, index):
        if index < self.num_chars - 1:
            self.entries[index + 1].focus_set()
            self.entries[index + 1].icursor(0)
        return 'break'  
    
    def _on_backspace(self, event, index):
        self.entries[index].delete(0, 'end')
        if index > 0:
            self.entries[index - 1].focus_set()
            self.entries[index - 1].icursor('end')
        return 'break'

    def _on_click(self, event, index):
        self.entries[index].focus_set()
        self.entries[index].after(1, lambda: self.entries[index].icursor('end'))

    def _on_focus_in(self, event, index):
        entry = self.entries[index]
        entry.icursor('end')
        if len(entry.get()) > 0:
            entry.config(highlightbackground=sg.fg, highlightcolor=sg.fg, highlightthickness=1, insertbackground=sg.bg_entry)
        else:
            self._start_blink(index)

    def _on_focus_out(self, event, index):
        entry = self.entries[index]
        entry.config(highlightthickness=0, insertbackground=sg.bg_entry)
        self._stop_blink(index)

    def _start_blink(self, index):
        self._stop_blink(index) 
        self._blink_state = True
        self._do_blink(index)

    def _stop_blink(self, index):
        if index < len(self.blink_jobs) and self.blink_jobs[index]:
            self.after_cancel(self.blink_jobs[index])
            self.blink_jobs[index] = None
        if index < len(self.entries):
            self.entries[index].config(bg=sg.bg_entry)

    def _do_blink(self, index):
        entry = self.entries[index]

        if len(entry.get()) == 0:
            if self._blink_state:
                entry.config(bg=sg.fg, insertbackground=sg.fg)  # Match cursor to background
            else:
                entry.config(bg=sg.bg_entry, insertbackground=sg.bg_entry)  # Match cursor to background
            self._blink_state = not self._blink_state

            while len(self.blink_jobs) <= index:
                self.blink_jobs.append(None)
            self.blink_jobs[index] = self.after(500, lambda: self._do_blink(index))
        else:
            self._stop_blink(index)
            entry.config(highlightbackground=sg.fg, highlightcolor=sg.fg, highlightthickness=0, insertbackground=sg.bg_entry)

    def get(self):
        return ''.join(entry.get() for entry in self.entries)

    def set(self, value):
        for i, entry in enumerate(self.entries):
            entry.delete(0, 'end')
            if i < len(value):
                entry.insert(0, value[i])

    def clear(self):
        for entry in self.entries:
            entry.delete(0, 'end')

def SectionContainer(parent, title, row, column, width, height):
    container = Frame(parent, bg=sg.bg)
    container.grid(row=row, column=column, padx=10, pady=10, sticky="w")

    outer_frame = Frame(container, bg=sg.fg, width=width, height=height)
    outer_frame.pack(fill="both", expand=True, pady=(10, 0))
    outer_frame.pack_propagate(False)  # Prevent width from changing

    frame = Frame(outer_frame, bg=sg.bg)
    frame.pack(padx=1, pady=1, fill="both", expand=True)

    label = Label(container,
                  text=title,
                  bg=sg.bg,
                  fg=sg.fg,
                  font=sg.font_header,
                  pady=0)
    label.place(relx=0.5, y=10, anchor="center")

    # Automatically apply unfocus behavior to the section
    bind_unfocus_on_click(frame)

    return frame


def bind_unfocus_on_click(root_widget):
    """
    Recursively bind all widgets in a container to unfocus entries when clicked.
    This makes clicking anywhere in the UI unfocus text boxes, like normal applications.

    Args:
        root_widget: The root widget/container to apply unfocus behavior to
    """
    def unfocus_entry(event):
        # Get the widget that was clicked
        clicked_widget = event.widget
        # Only unfocus if the clicked widget is not an Entry or similar input
        if not isinstance(clicked_widget, (Entry,)):
            root_widget.focus_set()

    def bind_recursive(widget):
        """Recursively bind all child widgets"""
        try:
            # Bind the click event to this widget
            widget.bind("<Button-1>", unfocus_entry, add="+")

            # Recursively bind all children
            for child in widget.winfo_children():
                bind_recursive(child)
        except Exception:
            pass  # Some widgets may not support binding

    bind_recursive(root_widget)


class FileListViewer(Frame):
    """A custom widget for viewing and managing CSV files in a directory"""

    def __init__(self, parent, directory="Saves/Data", width=400, height=300, **kwargs):
        super().__init__(parent, bg=sg.bg, width=width, height=height, **kwargs)
        self.pack_propagate(False)

        self.directory = directory
        self.selected_file = None
        self.file_labels = {}
        self.max_filename_length = 30
        self.last_file_list = []  # Track files to detect changes
        self.check_interval = 1000  # Check every 1 second (in milliseconds)

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        search_frame = Frame(self, bg=sg.bg)
        search_frame.pack(fill="x", padx=5, pady=5)

        Label(search_frame, text="Search:", bg=sg.bg, fg=sg.fg, font=sg.font_text).pack(side="left", padx=(0, 5))

        self.search_var = Entry(
            search_frame,
            font=sg.font_text,
            bg=sg.bg_entry,
            fg=sg.fg,
            insertbackground=sg.fg,
            highlightthickness=1,
            highlightbackground=sg.bg_entry,
            highlightcolor=sg.bg_entry,
            bd=0
        )
        self.search_var.pack(side="left", fill="x", expand=True)
        self.search_var.bind("<KeyRelease>", lambda e: self.refresh_file_list())

        list_frame = Frame(self, bg=sg.bg)
        list_frame.pack(fill="both", expand=True, padx=(5, 0), pady=5)

        self.canvas = Canvas(list_frame, bg=sg.bg, highlightthickness=0)

        # Create a custom styled scrollbar using ttk
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=sg.bg_entry,
            troughcolor=sg.bg,
            bordercolor=sg.fg,
            arrowcolor=sg.fg,
            darkcolor=sg.bg_entry,
            lightcolor=sg.bg_light
        )
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[('active', sg.fg), ('!active', sg.bg_entry)]
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.canvas.yview,
            style="Custom.Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y", padx=(8,0))

        self.scrollable_frame = Frame(self.canvas, bg=sg.bg)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Make scrollable_frame match canvas width
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)

        # Enable mouse wheel / trackpad scrolling
        self.bind_mouse_wheel()

        # Load files
        self.refresh_file_list()

        # Start auto-refresh to detect file changes
        self.start_auto_refresh()

    def refresh_file_list(self, force=False):
        """Refresh the list of CSV files"""
        # Get current file list
        try:
            current_files = sorted([f for f in os.listdir(self.directory) if f.endswith('.csv')])
        except Exception:
            current_files = []

        # Only refresh if files changed or forced
        if not force and current_files == self.last_file_list:
            return

        self.last_file_list = current_files

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.file_labels.clear()

        search_query = self.search_var.get().lower()

        try:
            files = current_files

            if search_query:
                files = [f for f in files if search_query in f.lower()]

            for filename in files:
                # Create border frame (initially no border)
                border_frame = Frame(self.scrollable_frame, bg=sg.bg, padx=0, pady=0)
                border_frame.pack(fill="x", pady=2)

                # Inner frame for the file label and buttons
                file_frame = Frame(border_frame, bg=sg.bg_entry)
                file_frame.pack(fill="x")

                # Truncate filename if too long
                display_name = filename
                if len(filename) > self.max_filename_length:
                    display_name = filename[:self.max_filename_length-3] + "..."

                # Delete button (rightmost)
                delete_border = Frame(file_frame, bg=sg.fg, padx=1, pady=1)
                delete_border.pack(side="right", padx=(0,0))

                delete_btn = Label(
                    delete_border,
                    text="Delete",
                    bg=sg.bg_entry,
                    fg=sg.fg,
                    font=sg.font_text,
                    padx=8,
                    pady=3,
                    cursor="hand2"
                )
                delete_btn.pack()
                delete_btn.bind("<Button-1>", lambda e, f=filename: self.delete_file(f))

                # Rename button (next to delete)
                rename_border = Frame(file_frame, bg=sg.fg, padx=1, pady=1)
                rename_border.pack(side="right", padx=(0, 2))

                rename_btn = Label(
                    rename_border,
                    text="Rename",
                    bg=sg.bg_entry,
                    fg=sg.fg,
                    font=sg.font_text,
                    padx=8,
                    pady=3,
                    cursor="hand2"
                )
                rename_btn.pack()
                rename_btn.bind("<Button-1>", lambda e, f=filename: self.rename_file(f))

                # File label on the left
                file_label = Label(
                    file_frame,
                    text=display_name,
                    bg=sg.bg_entry,
                    fg=sg.fg,
                    font=sg.font_text,
                    anchor="w",
                    padx=10,
                    pady=5,
                    cursor="hand2"
                )
                file_label.pack(side="left", fill="x", expand=True)
                file_label.bind("<Button-1>", lambda e, f=filename: self.select_file(f))

                self.file_labels[filename] = (border_frame, file_frame, file_label)

            # Re-bind mouse wheel to all new widgets
            self.bind_mouse_wheel()

        except Exception as e:
            print(f"Error loading files: {e}")

    def select_file(self, filename):
        # Deselect previous file - remove border
        if self.selected_file and self.selected_file in self.file_labels:
            border_frame, file_frame, label = self.file_labels[self.selected_file]
            border_frame.config(bg=sg.bg, padx=0, pady=0)
            file_frame.config(bg=sg.bg_entry)
            label.config(bg=sg.bg_entry, fg=sg.fg)

        # Select new file - add 1px sg.fg border
        self.selected_file = filename
        if filename in self.file_labels:
            border_frame, file_frame, label = self.file_labels[filename]
            border_frame.config(bg=sg.fg, padx=1, pady=1)
            file_frame.config(bg=sg.bg_light)
            label.config(bg=sg.bg_light, fg=sg.fg)

    def rename_file(self, filename):
        """Rename the specified file"""
        from tkinter import simpledialog, messagebox

        old_path = os.path.join(self.directory, filename)
        new_name = simpledialog.askstring("Rename File", "Enter new filename:", initialvalue=filename)

        if new_name and new_name != filename:
            if not new_name.endswith('.csv'):
                new_name += '.csv'

            new_path = os.path.join(self.directory, new_name)

            try:
                os.rename(old_path, new_path)
                self.selected_file = None
                self.refresh_file_list(force=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename file: {e}")

    def delete_file(self, filename):
        """Delete the specified file"""
        from tkinter import messagebox

        result = messagebox.askyesno("Delete File", f"Are you sure you want to delete '{filename}'?")

        if result:
            file_path = os.path.join(self.directory, filename)
            try:
                os.remove(file_path)
                self.selected_file = None
                self.refresh_file_list(force=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")

    def start_auto_refresh(self):
        """Start automatic refresh to detect file changes"""
        self.check_for_changes()

    def check_for_changes(self):
        """Check if files in directory have changed and refresh if needed"""
        try:
            self.refresh_file_list()
        except Exception:
            pass  # Silently ignore errors during auto-refresh

        # Schedule next check
        self.after(self.check_interval, self.check_for_changes)

    def bind_mouse_wheel(self):
        """Bind mouse wheel and trackpad scrolling"""
        def on_mouse_wheel(event):
            # macOS and Windows
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # Linux
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

        def bind_to_widget(widget):
            """Recursively bind mouse wheel to widget and all children"""
            widget.bind("<MouseWheel>", on_mouse_wheel)
            widget.bind("<Button-4>", on_mouse_wheel)
            widget.bind("<Button-5>", on_mouse_wheel)
            for child in widget.winfo_children():
                bind_to_widget(child)

        # Bind to the main widget and all its children
        bind_to_widget(self)