from dataclasses import dataclass, field
import tkinter as tk
from tkinter import simpledialog
from typing import List, Optional
from datetime import datetime, timedelta
import re


@dataclass
class Config:
    symbols: List[str]
    period: str
    short: int
    long: int
    start: Optional[str] = field(init=False, default=None)
    end: Optional[str] = field(init=False, default=None)
    figsize: tuple

    def __post_init__(self):
        self.end = datetime.now().strftime("%Y-%m-%d")
        self.start = self._calculate_start_date(self.period)

    def _calculate_start_date(self, period: str) -> Optional[str]:
        current_date = datetime.now()

        if period == "ytd":
            return f"{current_date.year}-01-01"
        elif period == "max":
            return "1990-01-01"  # Arbitrary early date for maximum range

        # Match patterns like "2d", "14d", "4mo", "3y"
        match = re.match(r"(\d+)([dmy])", period)
        if not match:
            raise ValueError(f"Invalid period format: {period}")

        value, unit = int(match.group(1)), match.group(2)

        # Convert the unit to a timedelta
        if unit == "d":  # Days
            delta = timedelta(days=value)
        elif unit == "m":  # Months (approximated as 30 days per month)
            delta = timedelta(days=value * 30)
        elif unit == "y":  # Years (approximated as 365 days per year)
            delta = timedelta(days=value * 365)
        else:
            raise ValueError(f"Unknown time unit: {unit}")

        start_date = current_date - delta
        return start_date.strftime("%Y-%m-%d")


def config_from_dialog() -> Config:
    root = tk.Tk()
    root.withdraw()

    symbols = simpledialog.askstring(
        "Input", "Enter stock symbol (e.g., DDOG MSFT VOO):"
    )
    period = simpledialog.askstring(
        "Input",
        "Enter period (e.g., 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max):",
        initialvalue="3y",
    )
    short_window = simpledialog.askinteger(
        "Input", "Enter short moving average window:", initialvalue=50
    )
    long_window = simpledialog.askinteger(
        "Input", "Enter long moving average window:", initialvalue=200
    )
    return Config(
        symbols=symbols.split(), period=period, short=short_window, long=long_window, figsize=(16, 16)
    )
