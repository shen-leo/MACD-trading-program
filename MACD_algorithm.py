import requests
import pandas as pd
import numpy as np
from math import floor
from termcolor import colored as cl
import matplotlib.pyplot as plt

plt.rcParams['figure.figsize'] = (20, 10)
plt.style.use('fivethirtyeight')


# function to retrieve the historical data from Alpha Vantage API
def get_historical_data(stock_ticker, start_date=None):
    api_key = open('api_key.txt', 'r')
    api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock_ticker}&apikey={api_key}'
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


# calculate components of the MACD indicator
def calculate_macd(price, slow, fast, smooth):
    ema1 = price.ewm(span=fast, adjust=False).mean()
    ema2 = price.ewm(span=slow, adjust=False).mean()
    macd = pd.DataFrame(ema1 - ema2).rename(columns={'close': 'macd'})
    signal = pd.DataFrame(macd.ewm(span=smooth, adjust=False).mean()).rename(columns={'macd': 'signal'})
    histogram = pd.DataFrame(macd['macd'] - signal['signal']).rename(columns={0: 'hist'})
    frames = [macd, signal, histogram]
    df = pd.concat(frames, join='inner', axis=1)
    return df


# plot for the MACD
def plot_macd(prices, macd, signal, histogram):
    ax1 = plt.subplot2grid((8, 1), (0, 0), rowspan=5, colspan=1)
    ax2 = plt.subplot2grid((8, 1), (5, 0), rowspan=3, colspan=1)

    ax1.plot(prices)
    ax2.plot(macd, color='grey', linewidth=1.5, label='MACD')
    ax2.plot(signal, color='skyblue', linewidth=1.5, label='SIGNAL')

    for i in range(len(prices)):
        if str(histogram[i])[0] == '-':
            ax2.bar(prices.index[i], histogram[i], color='#ef5350')
        else:
            ax2.bar(prices.index[i], histogram[i], color='#26a69a')

    plt.legend(loc='lower right')


# MACD strategy implementation
def implement_macd_strategy(prices, data):
    buy_price = [], sell_price = [], macd_signal = []
    signal = 0

    for i in range(len(data)):
        if data['macd'][i] > data['signal'][i]:
            if signal != 1:
                buy_price.append(prices[i])
                sell_price.append(np.nan)
                signal = 1
                macd_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                macd_signal.append(0)
        elif data['macd'][i] < data['signal'][i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices[i])
                signal = -1
                macd_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                macd_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            macd_signal.append(0)

    return buy_price, sell_price, macd_signal


# main function to drive the program
def main():
    ticker = input("Stock Ticker: ")
    date = input("Date: ")
    historical_data = get_historical_data(ticker, date)
    ticker_macd = calculate_macd(historical_data['close'], 26, 12, 9)
    ticker_macd.tail()
    plot_macd(historical_data['close'], ticker_macd['macd'], ticker_macd['signal'], ticker_macd['hist'])
    buy_price, sell_price, macd_signal = implement_macd_strategy(historical_data['close'], ticker_macd)


if __name__ == "__main__":
    main()
