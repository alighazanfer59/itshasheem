import streamlit as st
import json
import pandas as pd
import numpy as np
import ast  # Safely evaluate a string representation of a DataFrame
import aiohttp
import asyncio
import nest_asyncio

from backtest import run_backtest
from backtesting._stats import _Stats
import importlib
import traceback
import time
import os

yf = __import__("yfinance")  # Import yfinance dynamically
from datetime import datetime, timedelta

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from coinbase_data import fetch_all_historical_ohlcv, format_ohlcv_data
from trade_analysis import process_trades, display_trade_analysis
from metrics_display import display_metrics
from theme_manager import apply_theme, THEMES
from strategy_storage import save_strategy
from logger import get_logger

# import view_saved_strategies  # Import the saved strategies page
# from view_saved_strategies import show_saved_strategies_ui, switch_page
nest_asyncio.apply()
logger = get_logger(__name__)
# importlib.reload(view_saved_strategies)
st.set_page_config(page_title="Backtest UI", page_icon="📊")

# ✅ Apply theme from session state
if "selected_theme" in st.session_state:
    apply_theme(THEMES[st.session_state.selected_theme])

# Initialize session state variables if not set
if "loaded_strategy" not in st.session_state:
    st.session_state.loaded_strategy = None
if "results" not in st.session_state:
    st.session_state.results = None
if "df" not in st.session_state:
    st.session_state.df = None


# App Content Starts Here
st.title("📈 Backtest Trading Strategies")
st.sidebar.header("⚙️ Configure Your Strategy")
# Timeframe mapping for Yahoo Finance
TIMEFRAME_MAPPING = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h",
    "1d": "1d",
    "1w": "1wk",
    "1M": "1mo",
}

TIMEFRAME_LIMITS = {
    "1m": 60,
    "5m": 60,
    "15m": 60,
    "30m": 60,
    "1h": 730,
    "4h": 730,
    "1d": 730,
    "1w": 1460,
    "1M": 3650,
}

# Load Binance precisions file
with open("binance_precisions.json", "r") as f:
    binance_precisions = json.load(f)


# Function to get precision for a given Yahoo Finance symbol
def get_binance_precision(yahoo_symbol):
    """
    Maps Yahoo symbol (e.g., 'BTC-USD') to Binance's trading pair format and retrieves precision for 'BTCUSDT'.
    """
    binance_symbol = (
        yahoo_symbol.replace("-", "").upper() + "T"
    )  # Convert BTC-USD -> BTCUSDT
    return binance_precisions.get(binance_symbol, {}).get("amount_precision", 1)


# Load Strategies
def load_strategies():
    with open("str_params.json", "r") as f:
        return json.load(f)["strategies"]


strategies = load_strategies()

# Create a mapping {description: strategy_name}
strategy_mapping = {v["description"]: k for k, v in strategies.items()}


def get_valid_date_range(timeframe):
    days_limit = TIMEFRAME_LIMITS.get(timeframe, 730)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days_limit - 1)
    return start_date, end_date


# Initialize session state variables
# Session state defaults
for key in ["show_backtest", "run_backtest", "data_source", "df", "rerun"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "df" else False

# Streamlit Sidebar
st.sidebar.header("Strategy Selection")
selected_description = st.sidebar.selectbox(
    "Select Strategy", list(strategy_mapping.keys())
)
selected_strategy = strategy_mapping[selected_description]

# **Data Source Selection**
st.sidebar.subheader("📡 Data Source")
st.sidebar.markdown(
    """
    - **Live Data**: Fetch historical data from Yahoo Finance.
    - **Upload CSV**: Upload your own CSV file with historical data.
    """
)

data_source = st.sidebar.radio("Select Data Source", ["Live Data", "Upload CSV"])

df = None  # Placeholder for DataFrame
# Check if data source is changed and reset data
if st.session_state.data_source != data_source:
    st.session_state.df = None  # Clear Data Preview
    st.session_state.show_backtest = False  # Hide Backtest Button
    st.session_state.data_source = data_source  # Update selected source
    # st.session_state.updated_indicators = indicators.copy()  # Reset indicators
    st.rerun()  # Force rerun
# Live Data Sources
if data_source == "Live Data":
    st.sidebar.subheader("🌐 Choose Live Data Source")
    live_source = st.sidebar.selectbox(
        "Select Source", ["Yahoo Finance", "Coinbase"], index=0
    )

    if live_source == "Yahoo Finance":
        st.sidebar.write("**Yahoo Finance Selected**")
        # Input field for the symbol with a placeholder and help text
        symbol = st.sidebar.text_input(
            "Enter Symbol",
            value="BTC-USD",  # Default value
            help="Type the asset's ticker symbol. Example: BTC-USD for Bitcoin, AAPL for Apple.",
        )

        default_timeframe = "1h"  # Change this to your desired default timeframe
        timeframe_list = list(TIMEFRAME_MAPPING.keys())

        default_index = (
            timeframe_list.index(default_timeframe)
            if default_timeframe in timeframe_list
            else 0
        )

        # Timeframe selection box with help text
        new_timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            timeframe_list,
            key="timeframe",
            index=default_index,
            help="Choose the time interval for the data. Example: '1h' for hourly, '1d' for daily, etc.",
        )

        # Check if timeframe changed and reset data
        if "selected_timeframe" not in st.session_state:
            st.session_state.selected_timeframe = None

        if st.session_state.selected_timeframe != new_timeframe:
            st.session_state.df = None  # Clear previously fetched data
            st.session_state.show_backtest = False  # Hide backtest button
            st.session_state.selected_timeframe = (
                new_timeframe  # Update selected timeframe
            )
            st.rerun()  # Force rerun

    elif live_source == "Coinbase":
        # st.sidebar.write("**Coinbase Selected**")
        # Help text for symbol input
        st.sidebar.write(
            "**Symbol (e.g., BTC-USD)**: Enter the ticker symbol for the asset you want to fetch data for (e.g., BTC-USD for Bitcoin)."
        )

        # Input field for the symbol with a placeholder and help text
        symbol = st.sidebar.text_input(
            "Enter Symbol",
            value="BTC-USD",  # Default value
            help="Type the asset's ticker symbol (e.g., BTC-USD for Bitcoin, ETH-USD for Ethereum).",
        )

        # Granularity selection for Coinbase
        granularity_options = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "6h": 21600,
            "1d": 86400,
        }

        # Mapping the selected timeframe to Coinbase granularity
        coinbase_granularity_map = {
            "1m": "1 Minute",
            "5m": "5 Minutes",
            "15m": "15 Minutes",
            "1h": "1 Hour",
            "6h": "6 Hours",
            "1d": "1 Day",
        }

        # Granularity selection with a description
        granularity_str = st.sidebar.selectbox(
            "Select Granularity",
            list(coinbase_granularity_map.values()),
            index=3,  # Default to "1 Hour"
            help="Choose the granularity (time interval) for the data. Smaller intervals like '1m' provide more detailed data.",
        )

        new_timeframe = [
            k for k, v in coinbase_granularity_map.items() if v == granularity_str
        ][0]
        granularity = granularity_options[new_timeframe]

        # Display the selected granularity and corresponding seconds
        st.sidebar.write(
            f"**Selected Granularity**: {granularity_str} ({granularity} seconds)",
            help="The granularity defines the time duration between each data point. For example, '1m' represents 1-minute intervals.",
        )

        # Default number of days based on granularity
        default_days_mapping = {
            "1m": 7,  # 7 days of minute data
            "5m": 30,  # 30 days of 5-minute data
            "15m": 60,  # 60 days of 15-minute data
            "1h": 180,  # 180 days of hourly data
            "6h": 365,  # 365 days of 6-hour data
            "1d": 1000,  # 1000 days of daily data
        }

        default_num_days = default_days_mapping.get(new_timeframe, 180)

        # Help text for the number of days input
        st.sidebar.write(
            "**Number of Days**: Select the number of days of data you want to retrieve based on the granularity."
        )

        # User input for number of days with default value based on granularity
        num_days = st.sidebar.number_input(
            "Select Number of Days",
            min_value=1,
            max_value=1000,
            value=default_num_days,
            help="The number of days to fetch data for. The default value is based on the selected granularity.",
        )

        # Check if timeframe changed and reset data
        if "selected_timeframe" not in st.session_state:
            st.session_state.selected_timeframe = None

        if st.session_state.selected_timeframe != new_timeframe:
            st.session_state.df = None  # Clear previously fetched data
            st.session_state.show_backtest = False  # Hide backtest button
            st.session_state.selected_timeframe = (
                new_timeframe  # Update selected timeframe
            )
            st.rerun()  # Force rerun
    # else:
    #     st.warning("Binance not incorporated yet")

elif data_source == "Upload CSV":
    # Define the directory where CSV files are stored on the server
    SERVER_CSV_FOLDER = "/home/ubuntu/myApp/ohlcv_data"  # Change this path if needed

    # Ensure session state variables exist
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "df" not in st.session_state:
        st.session_state.df = None

    st.sidebar.markdown(
        "**Note**: Ensure your CSV file has the required columns: Date, Open, High, Low, Close, Volume."
    )

    # 📂 Select Data Source
    data_source = st.sidebar.radio(
        "📂 Select Data Source", ["Upload from Local", "Select from Server"]
    )

    # 🟢 Option 1: Upload from Local Machine
    if data_source == "Upload from Local":
        uploaded_file = st.sidebar.file_uploader("📂 Upload CSV File", type=["csv"])

        if (
            uploaded_file is not None
            and uploaded_file != st.session_state.selected_file
        ):
            st.session_state.selected_file = uploaded_file
            st.session_state.df = pd.read_csv(uploaded_file)

    # 🔵 Option 2: Select CSV from Server
    elif data_source == "Select from Server":
        try:
            csv_files = [f for f in os.listdir(SERVER_CSV_FOLDER) if f.endswith(".csv")]
        except FileNotFoundError:
            st.error(f"Folder '{SERVER_CSV_FOLDER}' not found.")
            csv_files = []

        selected_file = st.sidebar.selectbox(
            "📂 Select CSV File from Server", csv_files
        )

        if selected_file and selected_file != st.session_state.get("selected_file"):
            st.session_state.selected_file = selected_file
            file_path = os.path.join(SERVER_CSV_FOLDER, selected_file)

            try:
                df_raw = pd.read_csv(file_path)
                df_clean = df_raw.copy()

                # 🧠 Flexible time column detection
                time_candidates = ["date", "datetime", "timestamp", "time"]
                time_col = next(
                    (col for col in df_clean.columns if col.lower() in time_candidates),
                    None,
                )

                if not time_col:
                    raise ValueError(f"Missing time column. Tried: {time_candidates}")

                # 🧭 Map all expected columns dynamically
                expected = ["Open", "High", "Low", "Close", "Volume"]
                col_mapping = {}

                # Time column mapping
                col_mapping[time_col] = "Date"

                # Map OHLCV columns (case-insensitive match)
                for col in expected:
                    match = next(
                        (c for c in df_clean.columns if c.lower() == col.lower()), None
                    )
                    if match:
                        col_mapping[match] = col
                    else:
                        raise ValueError(f"Missing expected column: {col}")

                # 🔄 Apply standard names
                df_clean.rename(columns=col_mapping, inplace=True)

                # ✅ Now safely subset to just the needed columns
                required_cols = ["Date"] + expected
                if not all(col in df_clean.columns for col in required_cols):
                    raise ValueError(
                        f"After renaming, missing required columns: {required_cols}"
                    )

                df_clean = df_clean[required_cols].copy()

                # 🧼 Convert columns
                for col in expected:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

                df_clean["Date"] = pd.to_datetime(df_clean["Date"], errors="coerce")
                df_clean.set_index("Date", inplace=True)

                # 🚿 Drop NaNs
                before = len(df_clean)
                df_clean.dropna(inplace=True)
                after = len(df_clean)
                dropped = before - after

                logger.info(
                    f"[{selected_file}] Dropped {dropped} rows during cleaning."
                )
                logger.info(f"[{selected_file}] Column mapping used: {col_mapping}")

                # ✅ Save to session
                st.session_state.df = df_clean
                st.session_state.show_backtest = True

                st.success(f"✅ Loaded and cleaned '{selected_file}' successfully!")

            except Exception as e:
                st.session_state.df = None
                st.session_state.show_backtest = False
                logger.error(f"Error processing server CSV '{selected_file}': {str(e)}")
                logger.error("Traceback:\n" + traceback.format_exc())
                st.error(f"❌ Error processing CSV: {str(e)}")

# Fetch Data Button (Only for Live Data)
if data_source == "Live Data":
    if st.button("📥 Fetch Data"):
        if not symbol:
            st.warning("⚠️ Please enter a valid symbol.")
        else:
            try:
                if live_source == "Yahoo Finance":
                    st.markdown("### 📊 Fetching data for **Yahoo Finance**...")
                    # Date range for Yahoo Finance
                    start_date, end_date = get_valid_date_range(new_timeframe)
                    # Make the information more appealing with a combination of text and markdown formatting
                    st.markdown(f"### 📅 Date Range")
                    st.markdown(
                        f"**Start Date**: {start_date.strftime('%Y-%m-%d')}  |  **End Date**: {end_date.strftime('%Y-%m-%d')}"
                    )

                    st.markdown("### 🏷️ Symbol")
                    st.markdown(f"**Selected Symbol**: {symbol}")

                    # Check for missing inputs
                    if not symbol:
                        st.warning(
                            "⚠️ Please enter a valid symbol before fetching data."
                        )
                    elif not new_timeframe:
                        st.warning("⚠️ Please select a timeframe before fetching data.")
                    else:

                        interval = TIMEFRAME_MAPPING[new_timeframe]
                        st.write(f"Interval Selected: {interval}")

                        try:
                            # Download data from Yahoo Finance
                            df = yf.download(
                                symbol,
                                start=start_date,
                                end=end_date,
                                interval=TIMEFRAME_MAPPING.get(
                                    new_timeframe
                                ),  # Ensure interval is mapped correctly
                                auto_adjust=True,
                            )

                            # Check if data is fetched successfully
                            if df.empty:
                                st.error(
                                    "Failed to retrieve data. Please check the symbol, timeframe, and date range."
                                )
                            else:
                                df.reset_index(inplace=True)
                                if "Datetime" in df.columns:
                                    df.rename(
                                        columns={"Datetime": "Date"}, inplace=True
                                    )
                                df.columns = [
                                    "Date",
                                    "Open",
                                    "High",
                                    "Low",
                                    "Close",
                                    "Volume",
                                ]
                                df.set_index("Date", inplace=True)
                                df.index = pd.to_datetime(
                                    df.index
                                )  # Ensure Date column is in datetime format
                                st.session_state.df = df
                                st.session_state.show_backtest = (
                                    True  # Show backtest button after fetching data
                                )
                                s_msg = st.success("✅ Data fetched successfully!")
                                time.sleep(2)  # Delay for 2 seconds
                                s_msg.empty()  # Clear the success message

                        except ValueError as ve:
                            st.error(
                                f"ValueError: {ve} - There may be an issue with the symbol or timeframe."
                            )
                        except ConnectionError as ce:
                            st.error(
                                f"ConnectionError: {ce} - Could not connect to Yahoo Finance. Please check your internet connection."
                            )
                        except TimeoutError as te:
                            st.error(
                                f"TimeoutError: {te} - The request timed out. Please try again later."
                            )
                        except Exception as e:
                            # Catch any other unexpected errors
                            st.error(f"Unexpected error: {e}")

                elif live_source == "Coinbase":
                    if not symbol:
                        st.warning(
                            "⚠️ Please enter a valid symbol before fetching data."
                        )
                    else:
                        try:
                            # loop = asyncio.get_event_loop()
                            raw_data = asyncio.run(
                                fetch_all_historical_ohlcv(
                                    symbol, granularity, num_days
                                )
                            )
                            df = format_ohlcv_data(raw_data)

                            if df.empty:
                                st.error("❌ Failed to retrieve data from Coinbase.")
                            else:
                                st.session_state.df = df
                                st.session_state.show_backtest = True
                                st.success("✅ Coinbase data fetched successfully!")

                        except Exception as e:
                            st.error(f"Error fetching data from Coinbase: {e}")

                # elif live_source == "Other Source":
                #     warn_msg = st.warning("Other Source integration is pending.")
                #     time.sleep(2)
                #     warn_msg.empty()

                else:
                    st.warning("No live data source selected")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# Display Data Preview
if st.session_state.df is not None:
    st.subheader("📊 Data Preview")
    st.dataframe(st.session_state.df)


# Initialize General Trading Parameters in session state if not present
if "trading_params" not in st.session_state:
    st.session_state.trading_params = {
        "initial_cash": 10000,
        # "spread": 0.1,
        "commission": 0.001,
        "position_size": 1.0,
        "trade_mode": "Both",  # Default trade mode
    }

# --- Sidebar: General Settings ---
st.sidebar.subheader("Trading Parameters")
st.session_state.trading_params["initial_cash"] = st.sidebar.number_input(
    "Initial Capital", value=st.session_state.trading_params["initial_cash"]
)
# st.session_state.trading_params["spread"] = st.sidebar.number_input(
#     "Spread (%)", value=st.session_state.trading_params["spread"]
# )
percent_commission = st.sidebar.number_input(
    "Commission (%)",
    value=st.session_state.trading_params["commission"]
    * 100,  # Default value set as percentage
    format="%.3f",  # Display format for the percentage
    help="Enter the total effective cost (exchange fee + spread) as a percentage. For example, for 0.1% use 0.1 — the system will automatically convert it to 0.001.",
)

# Step 2: Convert the entered percentage to decimal
st.session_state.trading_params["commission"] = (
    percent_commission / 100
)  # Convert percentage to decimal


st.session_state.trading_params["position_size"] = st.sidebar.number_input(
    "Position Size (%)",
    value=20.0,  # Set default value to 20%
    min_value=0.1,
    max_value=99.99,
    step=0.1,
    help="Specify the position size as a percentage of the account balance. A higher value means taking larger trades, while a smaller value reduces exposure per trade.",
)

# Sidebar: Trade Mode Selection
new_trade_mode = st.sidebar.radio(
    "Select Trade Mode:",
    ["Long", "Short", "Both"],
    index=["Long", "Short", "Both"].index(
        st.session_state.trading_params["trade_mode"]
    ),
    key="trade_mode_input",
)

# Check if trade mode has changed and update session state
if new_trade_mode != st.session_state.trading_params["trade_mode"]:
    st.session_state.trading_params["trade_mode"] = new_trade_mode
    st.session_state.rerun = True  # Set rerun flag
    st.rerun()  # Force immediate UI refresh


if "strategy_config" not in st.session_state:
    st.session_state.strategy_config = strategies[selected_strategy]

strategy_config = st.session_state.strategy_config
# --- Strategy Selection ---
strategy_config = strategies[selected_strategy]
indicators = strategy_config["indicators"]

# Ensure State Persistence
if "updated_indicators" not in st.session_state:
    st.session_state.updated_indicators = {}

# Reset indicators when switching strategy
if st.session_state.get("last_strategy") != selected_strategy:
    st.session_state.updated_indicators = indicators.copy()
    st.session_state.last_strategy = selected_strategy  # Store the selected strategy

strategy_config.update(
    {
        "trade_mode": st.session_state.trading_params.get(
            "trade_mode", "Both"
        ),  # Ensure latest value is used
    }
)

# --- UI: Indicator Settings ---
st.subheader(f"{selected_description} - Indicator Settings")

# --- Use st.form to stop reruns until submit ---
with st.form(key="indicator_form"):
    new_values = {}

    for key, default_value in indicators.items():
        # Get stored value, defaulting to default_value
        value = st.session_state.updated_indicators.get(key, default_value)

        # Determine step dynamically: use float step if value is float
        step = 0.1 if isinstance(value, float) else 1

        new_values[key] = st.number_input(
            key.replace("_", " ").title(),
            value=value,  # Keep original value
            min_value=(
                0.0 if isinstance(value, float) else 0
            ),  # Ensure min_value matches type
            step=step,  # Dynamically adjust step
            key=f"indicator_{key}",
        )

    # Submit button inside form
    run_backtest_button = st.form_submit_button("🚀 Run Backtest")

# --- Process form submission outside of the form ---
if run_backtest_button:
    if st.session_state.df is None:
        warn_msg = st.warning("⚠️ Please fetch data before running the backtest.")
        time.sleep(2)
        warn_msg.empty()
        st.session_state.show_backtest = False  # Hide backtest button
        st.session_state.rerun = True  # Trigger UI refresh
    if st.session_state.df is not None:
        st.session_state.updated_indicators.update(new_values)
        success_msg = st.success("Indicator settings updated and backtest running!")
        logger.info("Preparing to run backtest...")

        if "df" not in st.session_state:
            logger.warning("No dataframe found in session_state.")
        if not st.session_state.get("df", pd.DataFrame()).shape[0]:
            logger.warning("Dataframe is empty.")
        if not selected_strategy:
            logger.warning("No strategy selected.")

        time.sleep(2)  # Delay for 2 seconds
        success_msg.empty()  # Clear the success message

        # st.subheader("📊 Data Preview")
        # st.dataframe(st.session_state.df)
        # Default values to prevent NameError
        live_source = None
        symbol = None
        new_timeframe = None

        # Ensure backtest is only shown when data is available
        if st.session_state.show_backtest and st.session_state.df is not None:
            logger.info(
                f"Running backtest for strategy: {selected_strategy} with parameters: {st.session_state.updated_indicators}"
            )
            strategy_config.update(
                {
                    "initial_cash": st.session_state.trading_params["initial_cash"],
                    "position_size": st.session_state.trading_params["position_size"],
                    "indicators": st.session_state.updated_indicators,
                    # "spread": st.session_state.trading_params["spread"],
                    "commission": st.session_state.trading_params["commission"],
                    # "trade_mode": st.session_state.trading_params["trade_mode"],
                    "precision_amount": (
                        get_binance_precision(symbol)
                        if data_source == "Live Data" and live_source == "Yahoo Finance"
                        else 1
                    ),
                    "symbol": symbol if data_source == "Live Data" else "CSV Data",
                    "timeframe": new_timeframe if data_source == "Live Data" else "N/A",
                }
            )

            max_price = st.session_state.df["Close"].max()
            initial_cash = st.session_state.trading_params["initial_cash"]
            # Ensure we can always buy at least 1000 units
            if initial_cash < max_price:
                position_size_factor = 1000
            elif initial_cash < max_price * 10:
                position_size_factor = 100
            elif initial_cash < max_price * 100:
                position_size_factor = 10
            else:
                position_size_factor = 1  # Full position size

            # st.write(st.session_state.df.dtypes)

            # st.write(
            #     "position_size_factor:",
            #     position_size_factor,
            #     type(position_size_factor),
            # )

            try:
                df = st.session_state.df / position_size_factor
                logger.info(
                    f"Running backtest with DataFrame columns: {df.columns.tolist()}"
                )
                logger.info(f"DataFrame shape: {df.shape}")
                logger.debug(f"First 5 rows of DataFrame:\n{df.head()}")

                logger.info(f"Selected strategy: {selected_strategy}")
                logger.debug(f"Strategy config: {strategy_config}")

                stats = run_backtest(df, selected_strategy, strategy_config)

                logger.info("Backtest completed successfully.")

            except Exception as e:
                logger.error(f"Error during backtest execution: {str(e)}")
                logger.error("Traceback:\n" + traceback.format_exc())
                st.error(f"Error during backtest execution: {str(e)}")

                stats = None  # Set stats to None on error

            # --- Display Results ---
            st.subheader("📊 Backtest Results")
            st.write(stats)
            st.session_state.run_backtest = True

            # --- Display Backtest Summary ---
            st.subheader("📊 Backtest Summary")

            # Ensure values are properly converted before displaying
            total_trades = int(stats.get("# Trades", 0))
            returns = float(stats.get("Return [%]", 0))
            win_rate = float(stats.get("Win Rate [%]", 0))
            final_equity = float(stats.get("Equity Final [$]", 0))
            max_drawdown = float(stats.get("Max. Drawdown [%]", 0))
            profit_factor = float(stats.get("Profit Factor", 0))
            sharpe_ratio = float(stats.get("Sharpe Ratio", 0) or 0)

            # Correct net profit calculation
            net_profit = final_equity - initial_cash

            # Display key metrics
            display_metrics(
                net_profit,
                win_rate,
                max_drawdown,
                profit_factor,
                sharpe_ratio,
                returns,
            )

            # Store parameters used in backtest
            st.session_state.loaded_params = strategy_config
            st.session_state.stats = stats if stats is not None else None

            if "_equity_curve" in stats:
                try:
                    equity_data = stats["_equity_curve"]
                    # If the data is already a DataFrame, use it directly
                    if isinstance(equity_data, pd.DataFrame):
                        equity_df = equity_data
                    elif isinstance(equity_data, str):
                        try:
                            # Convert the string back to a dictionary safely
                            equity_dict = ast.literal_eval(equity_data)
                            equity_df = pd.DataFrame(equity_dict)
                        except Exception as e:
                            st.error(f"Error processing equity curve: {e}")
                            equity_df = None
                    else:
                        st.error("Unexpected format for equity curve data.")
                        equity_df = None

                    # Plot the equity curve if data is valid
                    if equity_df is not None and "Equity" in equity_df.columns:
                        st.subheader("📈 Equity Curve")
                        fig = px.line(
                            equity_df,
                            x=equity_df.index,  # Use the index as the x-axis
                            y="Equity",
                            title="Equity Curve",
                            line_shape="linear",
                        )
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Equity Value",
                            template="plotly_dark",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Error processing equity curve: {e}")
                # Process trade data
                trades = process_trades(
                    stats, st.session_state.df, position_size_factor
                )
                # Display trade history and profit/loss analysis
                display_trade_analysis(trades, st.session_state.df)


def serialize_results(results):
    """Convert results to a JSON-serializable format."""
    if isinstance(results, pd.DataFrame):
        return results.astype(str).to_dict(
            orient="records"
        )  # Convert DataFrame to list of dicts

    elif isinstance(results, pd.Series):
        return results.astype(str).to_dict()  # Convert Series to a dict

    elif isinstance(results, dict):
        return {
            k: serialize_results(v) for k, v in results.items()
        }  # Recursively serialize dicts

    elif hasattr(results, "__dict__"):  # Handle custom objects
        return {k: serialize_results(v) for k, v in vars(results).items()}

    elif isinstance(results, pd.Timestamp):
        return results.isoformat()  # Convert Timestamp to ISO format string

    elif isinstance(results, pd.Timedelta):
        return str(results)  # Convert Timedelta to string

    return results  # Return as-is if already serializable


# Save Strategy UI
def save_strategy_ui():
    st.subheader("💾 Save Your Strategy")
    strategy_name = st.text_input("📌 Strategy Name", "")

    if (
        "loaded_params" in st.session_state
        and "df" in st.session_state
        and "stats" in st.session_state
    ):
        params = {
            **st.session_state.trading_params,  # Include trading parameters
            "indicators": st.session_state.updated_indicators,
        }
        df = st.session_state.df
        results = st.session_state.stats

        # Convert results to a JSON-serializable format
        results_serializable = serialize_results(results)

        if st.button("💾 Save Strategy"):
            if strategy_name:
                save_strategy(strategy_name, params, df, results_serializable)
                st.success(f"✅ Strategy '{strategy_name}' saved successfully!")
            else:
                st.error("⚠️ Please enter a strategy name.")
    else:
        st.warning("⚠️ No strategy data available to save.")


try:
    if "stats" in st.session_state and st.session_state.stats is not None:
        stats = st.session_state.stats
        # st.write("Type of stats:", type(stats))  # Check the type of stats

        # Check if stats is an instance of _Stats
        if isinstance(stats, _Stats):
            # st.write("Stats is an instance of _Stats.")
            save_strategy_ui()

        # Continue with other checks
        elif isinstance(stats, dict) and stats:
            save_strategy_ui()
        elif isinstance(stats, pd.Series) and not stats.empty and stats.any():
            save_strategy_ui()
        else:
            st.warning("⚠️ Stats is invalid.")
    # else:
    #     st.warning("⚠️ Stats not found in session state.")
except Exception as e:
    st.error(f"⚠️ Error occurred while validating stats: {e}")

if st.session_state.rerun:
    st.session_state.rerun = False
    st.rerun()

# --- Reset Button (Outside Form) ---
col1, col2, col3 = st.columns([1, 1, 1])
# col2 = st.columns([1, 2, 1])[0]
with col2:
    if st.button("🔄 Reset Data"):
        # Reset trading parameters
        st.session_state.trading_params = {
            "initial_cash": 10000,
            # "spread": 0.1,
            "commission": 0.001,
            "position_size": 1.0,
            "trade_mode": "Both",
        }

        # Reset indicator parameters
        # st.session_state.updated_indicators = strategies[selected_strategy][
        #     "indicators"
        # ].copy()
        st.session_state.updated_indicators = {}
        # Reset stored strategies
        st.session_state.df = None
        st.session_state.show_backtest = False
        st.session_state.loaded_params = None
        st.session_state.loaded_strategy = None
        # st.session_state.backtest_triggered = False
        # Trigger UI refresh
        st.session_state.rerun = True
        success_msg = st.success("✅ Data reset successfully!")
        time.sleep(2)
        success_msg.empty()
        st.rerun()


# # Render only the selected page
# if st.session_state.page == "Saved Strategies":
#     show_saved_strategies_ui()
# elif st.session_state.page == "Backtest":
#     show_backtest_ui()
