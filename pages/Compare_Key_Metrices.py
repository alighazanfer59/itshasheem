import streamlit as st
from strategy_storage import fetch_all_strategies, load_strategy
import pandas as pd
import plotly.express as px
from theme_manager import THEMES, apply_theme

st.set_page_config(page_title="Compare Strategy Results", page_icon="📁", layout="wide")

# ✅ Apply theme from session state
if "selected_theme" in st.session_state:
    apply_theme(THEMES[st.session_state.selected_theme])


st.title("📂 View & Compare Saved Strategies")

# Fetch saved strategies from DB
strategies = fetch_all_strategies()

if not strategies:
    st.warning("No strategies saved yet!")
    st.stop()

# 🎯 Select multiple strategies for comparison
selected_strategies = st.multiselect(
    "📊 Select Strategies to Compare",
    strategies,
    default=[],
)

# Load data for selected strategies
comparison_data = []

for strategy in selected_strategies:
    params, ohlcv_path, df, results = load_strategy(strategy)

    if results:
        comparison_data.append(
            {
                "Strategy": strategy,
                "Total Trades": results.get("# Trades", "N/A"),
                "Win %": results.get("Win Rate [%]", "N/A"),
                "Sharpe Ratio": results.get("Sharpe Ratio", "N/A"),
                "Max Drawdown %": results.get("Max. Drawdown [%]", "N/A"),
                "Net Profit %": results.get("Return [%]", "N/A"),
                "CAGR %": results.get("CAGR [%]", "N/A"),
                "Profit Factor": results.get("Profit Factor", "N/A"),
            }
        )

# Show comparison table
if comparison_data:
    st.subheader("📊 Strategy Comparison")

    # Convert list to DataFrame
    df_comparison = pd.DataFrame(comparison_data)

    # ✅ Allow user to choose view type (Horizontal / Vertical)
    view_type = st.radio(
        "Select View Type", ["Horizontal View", "Vertical View"], horizontal=True
    )

    if view_type == "Horizontal View":
        # ✅ METHOD 1: Display in Horizontal format
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison)

    elif view_type == "Vertical View":
        # ✅ METHOD 2: Display in Vertical format (Transposed)
        st.dataframe(df_comparison.T)  # Transpose to show metrics as rows

    # ✅ OPTIONAL: Custom CSS for better UI
    st.markdown(
        """
        <style>
        .stDataFrame { 
            overflow-x: auto;  /* Enable horizontal scroll if necessary */
            white-space: nowrap; /* Prevent text wrapping */
            max-width: 100%;  /* Ensure it fits container */
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # 📌 **Step 1: Allow user to select metric for visualization**
    st.subheader("📈 Compare Strategies with Graphs")
    metric_to_plot = st.selectbox(
        "Select a metric to compare",
        [
            "Total Trades",
            "Win %",
            "Sharpe Ratio",
            "Max Drawdown %",
            "Net Profit %",
            "CAGR %",
            "Profit Factor",
        ],
    )

    # 📌 **Step 2: Plot the selected metric**
    if metric_to_plot:
        fig = px.bar(
            df_comparison,
            x="Strategy",
            y=metric_to_plot,
            text=metric_to_plot,
            title=f"Comparison of {metric_to_plot}",
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(
            yaxis_title=metric_to_plot, xaxis_title="Strategy", showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
