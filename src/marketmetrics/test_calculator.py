import pandas as pd
from .calculator import calculate_rsi, calculate_macd


def test_calculate_rsi():
    prices = pd.Series(
        [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]
    )
    rsi = calculate_rsi(prices)
    assert len(rsi) == len(prices)
    assert not rsi.isna().all(), "RSI should not be NaN for all values"
    assert 0 <= rsi.iloc[-1] <= 100, "RSI should be between 0 and 100"


def test_calculate_macd():
    prices = pd.Series(
        [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    )
    macd, signal = calculate_macd(prices)
    assert len(macd) == len(prices)
    assert len(signal) == len(prices)
    assert not macd.isna().all(), "MACD should not be NaN for all values"
    assert not signal.isna().all(), "Signal should not be NaN for all values"


def test_calculate_rsi_edge_case():
    prices = pd.Series([50] * 20)  # Flat prices
    rsi = calculate_rsi(prices)
    assert rsi[14:].isna().all(), "RSI should be NaN"


def test_calculate_macd_edge_case():
    prices = pd.Series([100] * 30)  # Flat prices
    macd, signal = calculate_macd(prices)
    assert (macd == 0).all(), "MACD should be 0 for a flat price series"
    assert (signal == 0).all(), "Signal line should be 0 for a flat price series"
