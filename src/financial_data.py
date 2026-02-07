"""Financial data fetching utilities."""

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from fredapi import Fred
import os

# Initialize FRED API (works without API key but with rate limits)
# To use your own API key, set FRED_API_KEY environment variable
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.environ.get('FRED_API_KEY', None)
fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None


def get_stock_returns(ticker, years=20, label="Stock"):
    """
    Fetch historical stock market returns for a given ticker.

    Args:
        ticker: Stock ticker symbol
        years: Number of years of historical data to fetch
        label: Label for the dataset

    Returns:
        dict with 'dates' and 'values' lists (compounded starting at 1)
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)

        # Calculate annual returns
        hist['Year'] = hist.index.year
        annual_data = hist.groupby('Year').agg({
            'Close': ['first', 'last']
        })

        annual_returns = []
        years_list = []

        for year in annual_data.index:
            first_price = annual_data.loc[year, ('Close', 'first')]
            last_price = annual_data.loc[year, ('Close', 'last')]
            annual_return = ((last_price - first_price) / first_price) * 100
            annual_returns.append(annual_return)
            years_list.append(year)

        # Calculate compounded values starting at 1
        compounded_values = [1.0]
        for return_pct in annual_returns:
            compounded_values.append(compounded_values[-1] * (1 + return_pct / 100))

        # Round values
        compounded_values = [round(v, 4) for v in compounded_values]

        return {
            'dates': [years_list[0] - 1] + years_list,  # Add starting year
            'values': compounded_values
        }
    except Exception as e:
        print(f"Error fetching {label} data: {e}")
        # Return sample data if fetch fails
        return get_sample_stock_data(years)


def get_sp500_returns(years=20):
    """Fetch S&P 500 returns."""
    return get_stock_returns("^GSPC", years, "S&P 500")


def get_us_total_market_returns(years=20):
    """Fetch US Total Stock Market returns (using VTI ETF as proxy)."""
    return get_stock_returns("VTI", years, "US Total Market")


def get_global_market_returns(years=20):
    """Fetch Global Stock Market returns (using VT ETF as proxy)."""
    return get_stock_returns("VT", years, "Global Market")


def get_inflation_data_from_fred(years=20):
    """
    Fetch real CPI data from FRED.

    Args:
        years: Number of years of historical data to fetch

    Returns:
        dict with 'dates' and 'values' lists (compounded starting at 1)
    """
    if not fred:
        print("FRED API key not set. Using fallback inflation data.")
        return get_fallback_inflation_data(years)

    try:
        # Fetch CPI data from FRED (CPIAUCSL = Consumer Price Index for All Urban Consumers)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365 + 365)  # Extra year for calculation

        cpi_data = fred.get_series('CPIAUCSL', start_date, end_date)

        # Get annual average CPI for each year
        cpi_data.index = pd.to_datetime(cpi_data.index)
        annual_cpi = cpi_data.groupby(cpi_data.index.year).mean()

        # Calculate year-over-year inflation rates
        years_list = []
        inflation_rates = []

        for i in range(1, len(annual_cpi)):
            year = annual_cpi.index[i]
            prev_cpi = annual_cpi.iloc[i-1]
            curr_cpi = annual_cpi.iloc[i]
            inflation_rate = ((curr_cpi - prev_cpi) / prev_cpi) * 100

            years_list.append(year)
            inflation_rates.append(inflation_rate)

        # Calculate compounded values starting at 1
        compounded_values = [1.0]
        for rate in inflation_rates:
            compounded_values.append(compounded_values[-1] * (1 + rate / 100))

        # Round values
        compounded_values = [round(v, 4) for v in compounded_values]

        return {
            'dates': [years_list[0] - 1] + years_list,
            'values': compounded_values
        }
    except Exception as e:
        print(f"Error fetching FRED data: {e}")
        return get_fallback_inflation_data(years)


def get_fallback_inflation_data(years=20):
    """Fallback inflation data when FRED is unavailable."""
    current_year = datetime.now().year
    start_year = current_year - years

    historical_inflation = {
        2024: 3.4, 2023: 4.1, 2022: 8.0, 2021: 4.7, 2020: 1.2,
        2019: 1.8, 2018: 2.4, 2017: 2.1, 2016: 1.3, 2015: 0.1,
        2014: 1.6, 2013: 1.5, 2012: 2.1, 2011: 3.2, 2010: 1.6,
        2009: -0.4, 2008: 3.8, 2007: 2.8, 2006: 3.2, 2005: 3.4,
        2004: 2.7, 2003: 2.3, 2002: 1.6, 2001: 2.8, 2000: 3.4,
    }

    dates = []
    rates = []

    for year in range(start_year, current_year + 1):
        if year in historical_inflation:
            dates.append(year)
            rates.append(historical_inflation[year])

    compounded_values = [1.0]
    for rate in rates:
        compounded_values.append(compounded_values[-1] * (1 + rate / 100))

    compounded_values = [round(v, 4) for v in compounded_values]

    return {
        'dates': [dates[0] - 1] + dates if dates else [],
        'values': compounded_values
    }


def get_inflation_data(years=20):
    """
    Fetch historical inflation data (CPI-based) from FRED.
    Falls back to hardcoded data if FRED is unavailable.

    Args:
        years: Number of years of historical data to fetch

    Returns:
        dict with 'dates' and 'values' lists (compounded starting at 1)
    """
    return get_inflation_data_from_fred(years)


def get_sample_stock_data(years=20):
    """Fallback sample data for stock returns."""
    current_year = datetime.now().year
    start_year = current_year - years

    sample_returns = {
        2024: 24.2,
        2023: 26.3,
        2022: -18.1,
        2021: 28.7,
        2020: 18.4,
        2019: 31.5,
        2018: -4.4,
        2017: 21.8,
        2016: 12.0,
        2015: 1.4,
        2014: 13.7,
        2013: 32.4,
        2012: 16.0,
        2011: 2.1,
        2010: 15.1,
        2009: 26.5,
        2008: -37.0,
        2007: 5.5,
        2006: 15.8,
        2005: 4.9,
        2004: 10.9,
        2003: 28.7,
    }

    dates = []
    returns = []

    for year in range(start_year, current_year + 1):
        if year in sample_returns:
            dates.append(year)
            returns.append(sample_returns[year])

    # Calculate compounded values starting at 1
    compounded_values = [1.0]
    for return_pct in returns:
        compounded_values.append(compounded_values[-1] * (1 + return_pct / 100))

    # Round values
    compounded_values = [round(v, 4) for v in compounded_values]

    return {
        'dates': [dates[0] - 1] + dates if dates else [],
        'values': compounded_values
    }
