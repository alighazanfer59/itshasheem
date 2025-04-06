import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def process_trades(stats, df, position_size_factor=1):
    """
    Processes trade data and returns a formatted DataFrame.

    Args:
        stats: Object containing trade data.
        df: DataFrame with market prices (used for precision).
        position_size_factor: Scaling factor for trade sizes.

    Returns:
        trades (pd.DataFrame): Processed trade data.
    """
    _trades = stats._trades
    trades = _trades.copy()  # Create a copy to prevent modifying the original dataframe

    # Determine decimal precision from the last Close price
    precision = len(str(df["Close"].iloc[-1]).split(".")[1])

    # Adjust prices based on position size factor
    trades["EntryPrice"] = trades["EntryPrice"].astype(float) * position_size_factor
    trades["ExitPrice"] = trades["ExitPrice"].astype(float) * position_size_factor

    # Adjust Stop Loss (SL), Take Profit (TP), and Trade Size
    trades["SL"] = trades["SL"] * position_size_factor
    trades["TP"] = trades["TP"] * position_size_factor
    trades["Size"] = trades["Size"] / position_size_factor

    # Drop unwanted columns if they exist
    for col in ["Entry_λ(C)", "Exit_λ(C)"]:
        if col in trades.columns:
            trades.drop(columns=[col], inplace=True)

    # Rename columns if they exist
    column_mapping = {
        "EntryTime": "Entry Date",
        "ExitTime": "Exit Date",
        "PnL": "Profit/Loss",
    }

    trades.rename(
        columns={k: v for k, v in column_mapping.items() if k in trades.columns},
        inplace=True,
    )

    # Ensure correct data types
    trades["Entry Date"] = pd.to_datetime(trades["Entry Date"])
    trades["Exit Date"] = pd.to_datetime(trades["Exit Date"])
    trades["Profit/Loss"] = trades["Profit/Loss"].astype(float)

    # **Fix: Check if 'Return' column exists before renaming**
    if "Return" in trades.columns:
        trades.rename(columns={"Return": "Return (%)"}, inplace=True)
    else:
        # If 'Return' column is missing, calculate it as (Profit / EntryPrice) * 100
        trades["Return (%)"] = (trades["Profit/Loss"] / trades["EntryPrice"]) * 100

    trades["Return (%)"] = trades["Return (%)"].astype(float)

    return trades


# def display_trade_analysis(trades):
#     """Displays trade history and profit/loss over time in Streamlit."""

#     if not trades.empty:
#         st.subheader("📜 Trade History")

#         # Ensure Profit/Loss and Return (%) are numeric before formatting
#         trades["Profit/Loss"] = trades["Profit/Loss"].astype(float)
#         trades["Return (%)"] = trades["Return (%)"].astype(float)

#         # Display DataFrame without formatting (Streamlit does not support formatted strings)
#         st.dataframe(trades)

#         # Profit/Loss Over Time Chart
#         st.subheader("💹 Profit/Loss Over Time")

#         # Ensure numeric type before cumulative sum
#         trades["Cumulative Profit"] = trades["Profit/Loss"].cumsum()

#         fig_pnl = go.Figure()
#         fig_pnl.add_trace(
#             go.Scatter(
#                 x=trades["Exit Date"],
#                 y=trades["Cumulative Profit"],
#                 mode="lines",
#                 name="Cumulative Profit",
#                 line=dict(color="lime", width=2),
#             )
#         )

#         fig_pnl.update_layout(
#             title="Profit/Loss Over Time",
#             xaxis_title="Date",
#             yaxis_title="Cumulative Profit ($)",
#             template="plotly_dark",
#             hovermode="x",
#         )

#         st.plotly_chart(fig_pnl, use_container_width=True)


def display_trade_analysis(trades, df):
    """Displays trade history and Buy & Hold vs Strategy Equity Curve in Streamlit."""
    # st.write("df.columns:", df.columns.tolist())

    if not trades.empty:
        st.subheader("📜 Trade History")

        # Ensure Profit/Loss and Return (%) are numeric
        trades["Profit/Loss"] = trades["Profit/Loss"].astype(float)
        trades["Return (%)"] = trades["Return (%)"].astype(float)

        # Display raw trade table
        st.dataframe(trades)

        # ---------------------------------------------
        # 📈 Buy & Hold vs Strategy Equity Curve
        # ---------------------------------------------
        st.subheader("📊 Equity Curve vs Buy & Hold")

        # Strategy Equity Curve
        trades["Cumulative Profit"] = trades["Profit/Loss"].cumsum()

        # Buy & Hold Curve (normalized to match starting capital)
        df = df.copy()
        # Step 2: Try to find the datetime column
        datetime_col = None
        for col in df.columns:
            if col.lower() in ["date", "time", "datetime"]:
                datetime_col = col
                break

        # Step 3: If not found, maybe it's in the index?
        if datetime_col is None and isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            datetime_col = df.columns[
                0
            ]  # Assume the datetime is the first column after reset

        # Step 4: If still not found, throw an error
        if datetime_col is None:
            st.error("❌ No datetime column found in the data.")
            return

        # Step 5: Standardize to 'Date' column
        df["Date"] = pd.to_datetime(df[datetime_col])
        df.set_index("Date", inplace=True)

        # Align with the first trade's entry date
        if not trades.empty:
            df = df[df.index >= trades["Entry Date"].min()]

        # df = df[df.index >= trades["Entry Date"].min()]  # Align with first trade

        start_price = df["Close"].iloc[0]
        df["Buy & Hold"] = (df["Close"] / start_price - 1) * trades[
            "Cumulative Profit"
        ].iloc[0]

        # Plot
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=trades["Exit Date"],
                y=trades["Cumulative Profit"],
                mode="lines",
                name="Strategy",
                line=dict(color="lime", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Buy & Hold"],
                mode="lines",
                name="Buy & Hold",
                line=dict(color="orange", width=2, dash="dot"),
            )
        )

        fig.update_layout(
            title="Equity Curve vs Buy & Hold Return",
            xaxis_title="Date",
            yaxis_title="Cumulative Return ($)",
            template="plotly_dark",
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)
