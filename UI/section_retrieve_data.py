from tkinter import Frame, Label, StringVar
import UI._style_guide as sg
from UI._trade_settings import time_interval_choices, time_period_choices
from UI.custom_widgets import StyledEntry, StyledCombobox, SegmentedEntry, ToggleButtons, SectionContainer, bind_unfocus_on_click
from Data.retrieve_data import retrieve_data


ENTRY_TICKER = None
TIME_TYPE = None
ENTRY_START_DATE = None
ENTRY_END_DATE = None
COMBO_TIME_PERIOD = None
COMBO_TIME_INTERVAL = None






def create_retrieve_data_section(tab, row, column, width, height):
 

    retreive_data_frame = SectionContainer(tab, "Retrieve Data", row, column, width, height)
    
    
    ################## Inside Container #############
    ###### Ticker Entry ######
    ticker_row = Frame(retreive_data_frame, bg=sg.bg)
    ticker_row.pack(fill="x", padx=10, pady= (20, 0), anchor="w")

    label_ticker = Label(ticker_row,
                        text="Ticker:",
                        bg=sg.bg, fg=sg.fg,
                        font=sg.font_text)
    label_ticker.pack(side="left", padx=(0, 5))

    global ENTRY_TICKER
    ENTRY_TICKER = SegmentedEntry(ticker_row, num_chars=5)
    ENTRY_TICKER.pack(side="left")

    ###### Time Type Radio Buttons ######
    time_type_row = Frame(retreive_data_frame, bg=sg.bg)
    time_type_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w")

    label_time_type = Label(time_type_row,
                            text="Time Type:",
                            bg=sg.bg, fg=sg.fg,
                            font=sg.font_text)
    label_time_type.pack(side="left", padx=(0, 5))

    global TIME_TYPE
    TIME_TYPE = StringVar(value="Period")



    ###### Date Range ######
    date_row = Frame(retreive_data_frame, bg=sg.bg)

    label_start_date = Label(date_row,
                            text="Start:",
                            bg=sg.bg, fg=sg.fg,
                            font=sg.font_text)
    label_start_date.pack(side="left", padx=(0, 5))

    global ENTRY_START_DATE
    ENTRY_START_DATE = StyledEntry(date_row, width=10)
    ENTRY_START_DATE.pack(side="left", padx=(0, 10))
    ENTRY_START_DATE.insert(0, "YYYY-MM-DD")

    label_end_date = Label(date_row,
                          text="End:",
                          bg=sg.bg, fg=sg.fg,
                          font=sg.font_text)
    label_end_date.pack(side="left", padx=(0, 5))

    global ENTRY_END_DATE
    ENTRY_END_DATE = StyledEntry(date_row, width=10)
    ENTRY_END_DATE.pack(side="left")
    ENTRY_END_DATE.insert(0, "YYYY-MM-DD")





    ####### Time Period ######
    period_row = Frame(retreive_data_frame, bg=sg.bg)
    period_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w")

    label_time_period = Label(period_row,
                              text="Period:",
                              bg=sg.bg, fg=sg.fg,
                              font=sg.font_text)
    label_time_period.pack(side="left", padx=(0, 5))

    global COMBO_TIME_PERIOD
    COMBO_TIME_PERIOD = StyledCombobox(period_row, time_period_choices, width=4)
    COMBO_TIME_PERIOD.set("1mo") 
    COMBO_TIME_PERIOD.pack(side="left")

    ####### Time Interval  ######
    interval_row = Frame(retreive_data_frame, bg=sg.bg)
    interval_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w")

    label_time_interval = Label(interval_row,
                                text="Interval:",
                                bg=sg.bg, fg=sg.fg,
                                font=sg.font_text)
    label_time_interval.pack(side="left", padx=(0, 5))

    global COMBO_TIME_INTERVAL
    COMBO_TIME_INTERVAL = StyledCombobox(interval_row, time_interval_choices, width=4)
    COMBO_TIME_INTERVAL.set("1d")  
    COMBO_TIME_INTERVAL.pack(side="left")


    period_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w", before=interval_row)

    def switch_time_mode():
        if TIME_TYPE.get() == "Period":
            date_row.pack_forget()
            period_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w", before=interval_row)
        else:
            period_row.pack_forget()
            date_row.pack(fill="x", padx=10, pady= (10, 0), anchor="w", before=interval_row)
        retreive_data_frame.update_idletasks()

    # Create toggle buttons and bind to switch mode
    time_type_toggle = ToggleButtons(time_type_row, "Period", "Date", TIME_TYPE, default="Period")
    time_type_toggle.pack(side="left")
    TIME_TYPE.trace_add("write", lambda *args: switch_time_mode())

    ####### Retrieve Button ######
    retrieve_button_row = Frame(retreive_data_frame, bg=sg.bg)
    retrieve_button_row.pack(fill="x", padx=10, pady=(20, 10))

    button_border = Frame(retrieve_button_row, bg=sg.fg, padx=1, pady=1)
    button_border.pack(anchor="center")

    retrieve_button = Label(
        button_border,
        text="Retrieve Data",
        bg=sg.bg_light,
        fg=sg.fg,
        font=sg.font_text,
        padx=20,
        pady=8,
        cursor="hand2"
    )
    retrieve_button.pack()

    def on_click(e):
        retrieve_button.config(bg=sg.bg_entry, fg=sg.fg)
        retrieve_button.after(100, lambda: retrieve_button.config(bg=sg.bg_light, fg=sg.fg))
        handle_retrieve_data()

    retrieve_button.bind("<Button-1>", on_click)
    







    # Bind click events to unfocus entries when clicking anywhere
    bind_unfocus_on_click(retreive_data_frame)

def handle_retrieve_data():
    retrieve_data(ENTRY_TICKER.get(),
                  TIME_TYPE.get(),
                  ENTRY_START_DATE.get(),
                  ENTRY_END_DATE.get(),
                  COMBO_TIME_PERIOD.get(),
                  COMBO_TIME_INTERVAL.get())