import requests
import pandas as pd
import numpy as np
from math import floor
from termcolor import colored as cl
import matplotlib.pyplot as plt

plt.rcParams['figure.figsize'] = (20, 10)
plt.style.use('fivethirtyeight')


# function to retrieve the historical data from Alpha Vantage API
def get_historical_data(symbol, start_date=None):
    api_key = open('api_key.txt', 'r')
    api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    raw_df = requests.get(api_url).json()
    df = pd.DataFrame(raw_df[f'Time Series (Daily)']).T
    df = df.rename(
        columns={'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. volume': 'volume'})
    for i in df.columns:
        df[i] = df[i].astype(float)
    df.index = pd.to_datetime(df.index)
    if start_date:
        df = df[df.index >= start_date]
    return df


# main function to drive the program
def main():
    ticker = input("Stock Ticker: \n")
    date = input("Date: \n")
    historical_data = get_historical_data(ticker, date)


if __name__ == "__main__":
    main()
