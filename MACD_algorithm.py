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
    buy_price = []
    sell_price = []
    macd_signal = []
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


# function to plot the trade list
def plot_trade_list(ticker, historical_data, ticker_macd, buy_price, sell_price):
    ax1 = plt.subplot2grid((8, 1), (0, 0), rowspan=5, colspan=1)
    ax2 = plt.subplot2grid((8, 1), (5, 0), rowspan=3, colspan=1)

    ax1.plot(historical_data['close'], color='skyblue', linewidth=2, label=ticker)
    ax1.plot(historical_data.index, buy_price, marker='^', color='green', markersize=10, label='BUY SIGNAL',
             linewidth=0)
    ax1.plot(historical_data.index, sell_price, marker='v', color='r', markersize=10, label='SELL SIGNAL', linewidth=0)
    ax1.legend()
    ax1.set_title(f'{ticker} MACD SIGNALS')
    ax2.plot(ticker_macd['macd'], color='grey', linewidth=1.5, label='MACD')
    ax2.plot(ticker_macd['signal'], color='skyblue', linewidth=1.5, label='SIGNAL')

    for i in range(len(ticker_macd)):
        if str(ticker_macd['hist'][i])[0] == '-':
            ax2.bar(ticker_macd.index[i], ticker_macd['hist'][i], color='#ef5350')
        else:
            ax2.bar(ticker_macd.index[i], ticker_macd['hist'][i], color='#26a69a')

    plt.legend(loc='lower right')
    plt.show()


# function to create a position with MACD
def create_position(macd_signal, historical_data, ticker_macd):
    position = []
    for i in range(len(macd_signal)):
        if macd_signal[i] > 1:
            position.append(0)
        else:
            position.append(1)

    for i in range(len(historical_data['close'])):
        if macd_signal[i] == 1:
            position[i] = 1
        elif macd_signal[i] == -1:
            position[i] = 0
        else:
            position[i] = position[i - 1]

    macd = ticker_macd['macd']
    signal = ticker_macd['signal']
    close_price = historical_data['close']
    macd_signal = pd.DataFrame(macd_signal).rename(columns={0: 'macd_signal'}).set_index(historical_data.index)
    position = pd.DataFrame(position).rename(columns={0: 'macd_position'}).set_index(historical_data.index)

    frames = [close_price, macd, signal, macd_signal, position]
    strategy = pd.concat(frames, join='inner', axis=1)

    return strategy


# function for back testing the model
def back_testing(ticker, strategy, historical_data, investment_value):
    ticker_return = pd.DataFrame(np.diff(historical_data['close'])).rename(columns={0: 'returns'})
    macd_strategy_ret = []

    for i in range(len(ticker_return)):
        try:
            returns = ticker_return['returns'][i] * strategy['macd_position'][i]
            macd_strategy_ret.append(returns)
        except ValueError:
            pass

    macd_strategy_ret_df = pd.DataFrame(macd_strategy_ret).rename(columns={0: 'macd_returns'})

    number_of_stocks = floor(investment_value / historical_data['close'][0])
    macd_investment_ret = []

    for i in range(len(macd_strategy_ret_df['macd_returns'])):
        returns = number_of_stocks * macd_strategy_ret_df['macd_returns'][i]
        macd_investment_ret.append(returns)

    macd_investment_ret_df = pd.DataFrame(macd_investment_ret).rename(columns={0: 'investment_returns'})
    total_investment_ret = round(sum(macd_investment_ret_df['investment_returns']), 2)
    profit_percentage = floor((total_investment_ret / investment_value) * 100)
    print(cl('Profit gained from the MACD strategy by investing $100k in {} : {}'.format(ticker, total_investment_ret),
             attrs=['bold']))
    print(cl('Profit percentage of the MACD strategy : {}%'.format(profit_percentage), attrs=['bold']))


# main function to drive the program
def main():
    ticker = input("Stock Ticker: ").upper()
    date = input("Date: ")
    investment_value = int(input("Investment Value: "))

    historical_data = get_historical_data(ticker, date)
    ticker_macd = calculate_macd(historical_data['close'], 26, 12, 9)
    ticker_macd.tail()

    plot_macd(historical_data['close'], ticker_macd['macd'], ticker_macd['signal'], ticker_macd['hist'])
    buy_price, sell_price, macd_signal = implement_macd_strategy(historical_data['close'], ticker_macd)
    plot_trade_list(ticker, historical_data, ticker_macd, buy_price, sell_price)

    strategy = create_position(macd_signal, historical_data, ticker_macd)
    back_testing(ticker, strategy, historical_data, investment_value)


if __name__ == "__main__":
    main()
