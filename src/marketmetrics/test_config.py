import pytest
from datetime import datetime, timedelta
from .config import Config


@pytest.mark.parametrize(
    "symbols, period, short, long, expected_start",
    [
        (["TEST"], "ytd", 20, 100, f"{datetime.now().year}-01-01"),
        (["TEST"], "max", 20, 100, "1990-01-01"),
        (
            ["TEST"],
            "2d",
            20,
            100,
            (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        ),
        (
            ["TEST"],
            "3m",
            20,
            100,
            (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        ),
        (
            ["TEST"],
            "1y",
            20,
            100,
            (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        ),
    ],
)
def test_config_start_date(symbols, period, short, long, expected_start):
    config = Config(
        symbols=symbols, period=period, short=short, long=long, figsize=(10, 10)
    )
    assert config.start == expected_start


def test_invalid_period():
    with pytest.raises(ValueError, match="Invalid period format: invalid"):
        Config(symbols=["TEST"], period="invalid", short=20, long=100, figsize=(10, 10))


def test_unknown_time_unit():
    with pytest.raises(ValueError, match="Invalid period format: 5w"):
        Config(symbols=["TEST"], period="5w", short=20, long=100, figsize=(10, 10))


@pytest.mark.parametrize(
    "period, expected_period_in_days",
    [
        ("2d", 2),
        ("3m", 90),
        ("1y", 365),
        ("3y", 3 * 365),
        ("5y", 5 * 365),
        ("10y", 10 * 365),
    ],
)
def test_config_delta_days(period, expected_period_in_days):
    config = Config(
        symbols=["TEST"], period=period, short=20, long=100, figsize=(10, 10)
    )
    assert config.period_in_days == expected_period_in_days
