import yfinance as yf
from datetime import datetime

def retrieve_data(ticker, time_type, start_date, end_date, time_period, time_interval):
    print("Retrieve Data")
    print(ticker, time_type, start_date, end_date, time_period, time_interval)
    if ticker == "":
        print("No ticker provided")
        return
    if time_type == "Date" and (start_date == "" or end_date == ""):
        print("No start or end date provided")
        return
    if time_type == "Date":
        if start_date > end_date:
            print("Start date is after end date")
            return
    if time_type == "Period" and time_period == "":
        print("No time period provided")
        return
    if time_type == "Period":
        data = yf.download(ticker, period=time_period, interval=time_interval)
    else:
        data = yf.download(ticker, start=start_date, end=end_date, interval=time_interval)
    print(data)
    save_data(data, ticker, time_type, time_period, start_date, end_date, time_interval)

def save_data(data, ticker, time_type, time_period, start_date, end_date, time_interval):
    data.to_csv(f"Data/Saves/{ticker}_{time_interval}_{time_period if time_type == "Period" else start_date + "_" + end_date}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")