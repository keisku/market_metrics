import argparse
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import signal
import sys
import pandas as pd
from .config import config_from_dialog, Config


def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, short_window=12, long_window=26, signal_window=9):
    short_ema = prices.ewm(span=short_window, adjust=False).mean()
    long_ema = prices.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal


def plot_stock_data(
    symbol: str,
    period: str,
    start: str,
    end: str,
    short_window: int,
    long_window: int,
):
    company = yf.Ticker(symbol)
    company_history = company.history(interval="1d", start=start, end=end)
    company_close_prices = company_history["Close"]
    company_volume = company_history["Volume"]

    short_ma = company_close_prices.rolling(window=short_window).mean()
    long_ma = company_close_prices.rolling(window=long_window).mean()
    golden_cross = (short_ma.shift(1) < long_ma.shift(1)) & (short_ma > long_ma)
    death_cross = (short_ma.shift(1) > long_ma.shift(1)) & (short_ma < long_ma)

    rsi = calculate_rsi(company_close_prices)
    macd, signal_line = calculate_macd(company_close_prices)

    max_price = company_close_prices.max()
    min_price = company_close_prices.min()
    mean_price = company_close_prices.mean()
    max_dates = company_close_prices[company_close_prices == max_price].index
    min_dates = company_close_prices[company_close_prices == min_price].index

    # Calculate Bollinger Bands
    rolling_mean = company_close_prices.rolling(window=20).mean()
    rolling_std = company_close_prices.rolling(window=20).std()
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)

    # Calculate Fibonacci retracement levels
    fib_levels = [
        max_price - (max_price - min_price) * level
        for level in [0.236, 0.382, 0.5, 0.618, 0.786]
    ]

    fig = plt.figure(figsize=(12, 24))
    ax1 = fig.add_subplot(6, 1, (1, 3))
    ax2 = fig.add_subplot(6, 1, 4)
    ax3 = fig.add_subplot(6, 1, 5)
    ax4 = fig.add_subplot(6, 1, 6)

    # Plotting stock price, moving averages, and Bollinger Bands
    ax1.plot(
        company_history.index,
        short_ma,
        label=f"{short_window} day MA",
        color="blue",
        linewidth=1,
    )
    ax1.plot(
        company_history.index,
        long_ma,
        label=f"{long_window} day MA",
        color="red",
        linewidth=1,
    )
    ax1.plot(
        company_history.index,
        company_close_prices,
        label="Closing",
        color="dimgrey",
        linewidth=1,
    )
    ax1.fill_between(
        company_history.index,
        lower_band,
        upper_band,
        color="darkgray",
        alpha=0.1,
        label="Bollinger Bands",
    )
    ax1.scatter(
        company_history.index[golden_cross],
        company_close_prices[golden_cross],
        color="green",
        marker="^",
        label="Golden Cross",
        edgecolors="black",
    )
    ax1.scatter(
        company_history.index[death_cross],
        company_close_prices[death_cross],
        color="red",
        marker="v",
        label="Death Cross",
        edgecolors="black",
    )

    # Scatter max, min, prices
    ax1.scatter(
        max_dates,
        [max_price] * len(max_dates),
        color="gold",
        marker="o",
        label="Max Price",
        edgecolors="black",
    )
    ax1.scatter(
        min_dates,
        [min_price] * len(min_dates),
        color="crimson",
        marker="o",
        label="Min Price",
        edgecolors="black",
    )
    ax1.axhline(mean_price, color="green", linewidth=1, label="Mean Price")

    # Plot Fibonacci retracement levels and add buy/sell signals
    for level, value in zip([0.236, 0.382, 0.5, 0.618, 0.786], fib_levels):
        ax1.axhline(
            value,
            linestyle="dotted",
            color="purple",
            linewidth=1,
            label=f"Fib {level * 100:.1f}%",
        )
        # Move the buy/sell signals slightly to the right for better visibility
        signal_date = company_history.index[-1] + pd.Timedelta(days=10)
        if company_close_prices.iloc[-1] > value:
            ax1.scatter(
                signal_date,
                value,
                color="green",
                marker="^",
                label=f"Buy Signal (Fib {level * 100:.1f}%)",
                edgecolors="black",
            )
        elif company_close_prices.iloc[-1] < value:
            ax1.scatter(
                signal_date,
                value,
                color="red",
                marker="v",
                label=f"Sell Signal (Fib {level * 100:.1f}%)",
                edgecolors="black",
            )

    ax1.set_title(f"{symbol} | {short_window} / {long_window} day MA | {period}")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Price")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.tick_params(axis="x", rotation=45)
    ax1.legend()
    ax1.grid(False)

    # Plotting RSI
    ax2.plot(
        company_history.index, rsi, label="RSI", color="cornflowerblue", linewidth=1
    )
    ax2.axhline(70, color="tomato", linestyle="dotted", label="Overbought (70)")
    ax2.axhline(30, color="forestgreen", linestyle="dotted", label="Oversold (30)")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("RSI")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax2.tick_params(axis="x", rotation=45)
    ax2.legend()
    ax2.grid(False)

    # Plotting Volume
    ax3.bar(company_history.index, company_volume, color="darkgray", label="Volume")
    ax3.plot(
        company_history.index,
        company_volume.rolling(window=short_window).mean(),
        label=f"{short_window} day Volume MA",
        color="blue",
        linestyle="dashed",
        linewidth=1,
    )
    ax3.plot(
        company_history.index,
        company_volume.rolling(window=long_window).mean(),
        label=f"{long_window} day Volume MA",
        color="red",
        linestyle="dashed",
        linewidth=1,
    )
    ax3.axhline(
        company_volume.mean(),
        color="green",
        linestyle="dashed",
        linewidth=1,
        label="Mean Volume",
    )
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Volume")
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax3.tick_params(axis="x", rotation=45)
    ax3.legend()
    ax3.grid(False)

    # Plotting MACD
    ax4.plot(company_history.index, macd, label="MACD", color="blue", linewidth=1)
    ax4.plot(
        company_history.index,
        signal_line,
        label="Signal Line",
        color="red",
        linestyle="dashed",
        linewidth=1,
    )
    golden_cross_macd = (macd.shift(1) < signal_line.shift(1)) & (macd > signal_line)
    death_cross_macd = (macd.shift(1) > signal_line.shift(1)) & (macd < signal_line)
    ax4.scatter(
        company_history.index[golden_cross_macd],
        macd[golden_cross_macd],
        color="green",
        marker="^",
        label="MACD Golden Cross",
        edgecolors="black",
    )
    ax4.scatter(
        company_history.index[death_cross_macd],
        macd[death_cross_macd],
        color="red",
        marker="v",
        label="MACD Death Cross",
        edgecolors="black",
    )
    ax4.axhline(5, color="gray", linestyle="dotted", linewidth=0.5)
    # Add horizontal lines at intervals of 5, starting from 10, only if the MACD value exceeds the previous threshold
    for value in range(10, 55, 5):
        if macd.max() > value - 5:
            ax4.axhline(value, color="gray", linestyle="dotted", linewidth=0.5)
    ax4.set_xlabel("Date")
    ax4.set_ylabel("MACD")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax4.tick_params(axis="x", rotation=45)
    ax4.legend()
    ax4.grid(False)

    # Adding hover functionality
    def format_coord(x, y):
        try:
            date = mdates.num2date(x).strftime("%Y-%m-%d")
            return f"Date: {date}, Value: {y:.2f}"
        except ValueError:
            return f"Date: {x:.2f}, Value: {y:.2f}"

    ax1.format_coord = format_coord
    ax2.format_coord = format_coord
    ax3.format_coord = format_coord
    ax4.format_coord = format_coord

    plt.tight_layout()
    plt.show(block=False)


def signal_handler(_sig, _frame):
    print("\nstock_analyzer is closing...")
    plt.close("all")
    sys.exit(0)


def main() -> int:
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Market Metrics: A Python application for technical stock market analysis."
    )
    parser.add_argument("--symbols", type=str, nargs="+", help="E.g., DDOG MSFT VOO")
    parser.add_argument(
        "--period",
        type=str,
        help="1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max",
    )
    parser.add_argument(
        "--short",
        type=int,
        nargs="+",
        help="Short window for moving average. E.g., 20 50",
    )
    parser.add_argument(
        "--long",
        type=int,
        nargs="+",
        help="Long window for moving average. E.g., 100 200",
    )
    parser.add_argument("--debug", type=bool, help="Enable debug mode", default=False)
    args = parser.parse_args()

    if args.debug:
        yf.enable_debug_mode()

    if args.symbols and args.period and args.short and args.long:
        config = Config(
            symbols=args.symbols, period=args.period, short=args.short, long=args.long
        )
    else:
        config = config_from_dialog()

    for symbol in config.symbols:
        plot_stock_data(
            symbol, config.period, config.start, config.end, config.short, config.long
        )

    plt.show()
    return 0
