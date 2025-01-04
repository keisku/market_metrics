import argparse
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import signal
import sys
import pandas as pd
import numpy as np
from .config import config_from_dialog, Config
from .calculator import calculate_rsi, calculate_macd


TRADING_DAYS_IN_YEAR = 252
NA_ANNUAL_VOLATILITY = 0.0
YEAR_IN_DAYS = 365


def plot_stock_data(
    symbol: str,
    period: str,
    period_in_days: int,
    start: str,
    end: str,
    short_window: int,
    long_window: int,
    figsize: tuple,
):
    company = yf.Ticker(symbol)
    company_history = company.history(interval="1d", start=start, end=end)
    company_close_prices: pd.Series = company_history["Close"]
    company_volume = company_history["Volume"]

    daily_volatility = company_close_prices.pct_change().std()
    annual_volatility = NA_ANNUAL_VOLATILITY
    if period_in_days >= YEAR_IN_DAYS:
        annual_volatility = daily_volatility * np.sqrt(TRADING_DAYS_IN_YEAR)

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

    fig = plt.figure(figsize=figsize)
    main_ax = fig.add_subplot(6, 1, (1, 3))
    rsi_ax = fig.add_subplot(6, 1, 4)
    volume_ax = fig.add_subplot(6, 1, 5)
    macd_ax = fig.add_subplot(6, 1, 6)

    # Plotting stock price, moving averages, and Bollinger Bands
    main_ax.plot(
        company_history.index,
        short_ma,
        label=f"{short_window} day MA",
        color="blue",
        linewidth=1,
    )
    main_ax.plot(
        company_history.index,
        long_ma,
        label=f"{long_window} day MA",
        color="red",
        linewidth=1,
    )
    main_closing_line = main_ax.plot(
        company_history.index,
        company_close_prices,
        label="Closing",
        color="dimgrey",
        linewidth=1,
    )
    main_ax.fill_between(
        company_history.index,
        lower_band,
        upper_band,
        color="darkgray",
        alpha=0.1,
        label="Bollinger Bands",
    )
    main_ax.scatter(
        company_history.index[golden_cross],
        company_close_prices[golden_cross],
        color="green",
        marker="^",
        label="Golden Cross",
        edgecolors="black",
    )
    main_ax.scatter(
        company_history.index[death_cross],
        company_close_prices[death_cross],
        color="red",
        marker="v",
        label="Death Cross",
        edgecolors="black",
    )
    main_ax.scatter(
        max_dates,
        [max_price] * len(max_dates),
        color="gold",
        marker="o",
        label="Max Price",
        edgecolors="black",
    )
    main_ax.scatter(
        min_dates,
        [min_price] * len(min_dates),
        color="crimson",
        marker="o",
        label="Min Price",
        edgecolors="black",
    )
    main_ax.axhline(mean_price, color="green", linewidth=1, label="Mean Price")

    # Plot Fibonacci retracement levels and add buy/sell signals
    for level, value in zip([0.236, 0.382, 0.5, 0.618, 0.786], fib_levels):
        main_ax.axhline(
            value,
            linestyle="dotted",
            color="purple",
            linewidth=1,
            label=f"Fib {level * 100:.1f}%",
        )
        # Move the buy/sell signals slightly to the right for better visibility
        signal_date = company_history.index[-1] + pd.Timedelta(days=10)
        if company_close_prices.iloc[-1] > value:
            main_ax.scatter(
                signal_date,
                value,
                color="green",
                marker="^",
                label=f"Buy Signal (Fib {level * 100:.1f}%)",
                edgecolors="black",
            )
        elif company_close_prices.iloc[-1] < value:
            main_ax.scatter(
                signal_date,
                value,
                color="red",
                marker="v",
                label=f"Sell Signal (Fib {level * 100:.1f}%)",
                edgecolors="black",
            )

    base_title = f"{symbol} | {short_window} / {long_window} day MA | {period}"
    if annual_volatility == NA_ANNUAL_VOLATILITY:
        main_ax.set_title(f"{base_title} | Daily Volatility {daily_volatility:.4f}")
    else:
        main_ax.set_title(
            f"{base_title} | Volatility Daily {daily_volatility * 100:.2f}% Annual {annual_volatility * 100:.2f}%"
        )
    main_ax.set_xlabel("Date")
    main_ax.set_ylabel("Price")
    main_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    main_ax.tick_params(axis="x", rotation=45)
    main_ax.legend()
    main_ax.grid(False)
    main_closing_cursor = mplcursors.cursor(main_closing_line, hover=True)
    main_closing_cursor.connect(
        event="add",
        func=lambda sel: [
            sel.annotation.set_text(
                f"{mdates.num2date(sel.target[0]).strftime('%Y-%m-%d')} : {sel.target[1]:.2f}"
            ),
            sel.annotation.set_bbox(
                dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white")
            ),
        ],
    )

    # Plotting RSI
    rsi_line = rsi_ax.plot(
        company_history.index,
        rsi,
        label="Relative Strength Index (RSI)",
        color="cornflowerblue",
        linewidth=1,
    )
    rsi_ax.axhline(70, color="tomato", linestyle="dotted", label="Overbought (70)")
    rsi_ax.axhline(30, color="forestgreen", linestyle="dotted", label="Oversold (30)")
    rsi_ax.set_xlabel("Date")
    rsi_ax.set_ylabel("RSI")
    rsi_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    rsi_ax.tick_params(axis="x", rotation=45)
    rsi_ax.legend()
    rsi_ax.grid(False)
    rsi_cursor = mplcursors.cursor(rsi_line, hover=True)
    rsi_cursor.connect(
        event="add",
        func=lambda sel: [
            sel.annotation.set_text(
                f"{mdates.num2date(sel.target[0]).strftime('%Y-%m-%d')} : {sel.target[1]:.2f}"
            ),
            sel.annotation.set_bbox(
                dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white")
            ),
            sel.annotation.update(
                {
                    "color": "forestgreen"
                    if sel.target[1] <= 30
                    else "tomato"
                    if sel.target[1] >= 70
                    else "cornflowerblue"
                }
            ),
        ],
    )

    # Plotting Volume
    volume_line = volume_ax.bar(
        company_history.index, company_volume, color="darkgray", label="Volume"
    )
    volume_ax.plot(
        company_history.index,
        company_volume.rolling(window=5).mean(),
        label="5 day Volume MA",
        color="blue",
        linestyle="dashed",
        linewidth=1,
    )
    volume_ax.plot(
        company_history.index,
        company_volume.rolling(window=50).mean(),
        label="50 day Volume MA",
        color="red",
        linestyle="dashed",
        linewidth=1,
    )
    volume_ax.axhline(
        company_volume.mean(),
        color="green",
        linestyle="dashed",
        linewidth=1,
        label="Mean Volume",
    )
    volume_ax.set_xlabel("Date")
    volume_ax.set_ylabel("Volume")
    volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    volume_ax.tick_params(axis="x", rotation=45)
    volume_ax.legend()
    volume_ax.grid(False)
    volume_cursor = mplcursors.cursor(volume_line, hover=True)
    volume_cursor.connect(
        event="add",
        func=lambda sel: [
            sel.annotation.set_text(
                f"{mdates.num2date(sel.target[0]).strftime('%Y-%m-%d')} : {sel.target[1]:.2f}"
            ),
            sel.annotation.set_bbox(
                dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white")
            ),
        ],
    )

    # Plotting MACD
    macd_line = macd_ax.plot(
        company_history.index, macd, label="MACD", color="blue", linewidth=1
    )
    macd_ax.plot(
        company_history.index,
        signal_line,
        label="Signal Line",
        color="red",
        linestyle="dashed",
        linewidth=1,
    )
    golden_cross_macd = (macd.shift(1) < signal_line.shift(1)) & (macd > signal_line)
    death_cross_macd = (macd.shift(1) > signal_line.shift(1)) & (macd < signal_line)
    macd_ax.scatter(
        company_history.index[golden_cross_macd],
        macd[golden_cross_macd],
        color="green",
        marker="^",
        label="MACD Golden Cross",
        edgecolors="black",
    )
    macd_ax.scatter(
        company_history.index[death_cross_macd],
        macd[death_cross_macd],
        color="red",
        marker="v",
        label="MACD Death Cross",
        edgecolors="black",
    )
    macd_ax.axhline(5, color="gray", linestyle="dotted", linewidth=0.5)
    # Add horizontal lines at intervals of 5, starting from 10, only if the MACD value exceeds the previous threshold
    for value in range(10, 55, 5):
        if macd.max() > value - 5:
            macd_ax.axhline(value, color="gray", linestyle="dotted", linewidth=0.5)
    macd_ax.set_xlabel("Date")
    macd_ax.set_ylabel("MACD")
    macd_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    macd_ax.tick_params(axis="x", rotation=45)
    macd_ax.legend()
    macd_ax.grid(False)
    macd_cursor = mplcursors.cursor(macd_line, hover=True)
    macd_cursor.connect(
        event="add",
        func=lambda sel: [
            sel.annotation.set_text(
                f"{mdates.num2date(sel.target[0]).strftime('%Y-%m-%d')} : {sel.target[1]:.2f}"
            ),
            sel.annotation.set_bbox(
                dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white")
            ),
        ],
    )

    plt.tight_layout()
    plt.show(block=False)


def main() -> int:
    def signal_handler(_sig, _frame):
        plt.close("all")
        sys.exit(0)

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
        help="Short window for moving average. E.g., 20, 50",
    )
    parser.add_argument(
        "--long",
        type=int,
        help="Long window for moving average. E.g., 100, 200",
    )
    parser.add_argument(
        "--figsize",
        type=int,
        nargs=2,
        help="Figure size in inches. E.g., 16 16",
        default=(16, 16),
    )
    parser.add_argument("--debug", type=bool, help="Enable debug mode", default=False)
    args = parser.parse_args()

    if args.debug:
        yf.enable_debug_mode()

    if args.symbols and args.period and args.short and args.long:
        config = Config(
            symbols=args.symbols,
            period=args.period,
            short=args.short,
            long=args.long,
            figsize=args.figsize,
        )
    else:
        config = config_from_dialog()

    for symbol in config.symbols:
        plot_stock_data(
            symbol,
            config.period,
            config.period_in_days,
            config.start,
            config.end,
            config.short,
            config.long,
            figsize=config.figsize,
        )

    plt.show()
    return 0
