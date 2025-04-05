import streamlit as st
from strategy_storage import fetch_all_strategies, load_strategy, delete_strategy
import time

# Clear session state when user navigates back to this page
if "page_loaded" not in st.session_state:
    st.session_state.page_loaded = True  # This will be set only once per session
else:
    for key in [
        "loaded_strategy",
        "loaded_params",
        "loaded_df",
        "loaded_results",
        "ohlcv_path",
        "show_delete_option",
    ]:
        if key in st.session_state:
            del st.session_state[key]


st.set_page_config(page_title="Saved Strategies", page_icon="📁", layout="wide")

st.title("📂 View Saved Strategies")

strategies = fetch_all_strategies()  # Fetch saved strategies from DB

if not strategies:
    st.warning("No strategies saved yet!")
    st.stop()

# Add a placeholder option at the beginning
strategy_options = ["Select a strategy..."] + strategies
selected_strategy = st.selectbox("🔍 Select Strategy", strategy_options, index=0)

# Buttons in columns
col1, col2 = st.columns([1, 1])

with col1:
    if selected_strategy != "Select a strategy...":
        if st.button("📤 Load Strategy"):
            st.session_state.loaded_strategy = (
                selected_strategy  # Store loaded strategy name
            )
            try:
                params, ohlcv_path, df, results = load_strategy(selected_strategy)

                if params and df is not None and results:
                    st.session_state.loaded_strategy = selected_strategy
                    st.session_state.loaded_params = params
                    st.session_state.ohlcv_path = ohlcv_path
                    st.session_state.loaded_df = (
                        df  # Save the loaded DataFrame to session state
                    )
                    st.session_state.loaded_results = (
                        results  # Save the backtest results to session state
                    )
                    st.session_state.show_delete_option = (
                        False  # Reset delete confirmation
                    )
                else:
                    st.error("Failed to load strategy. Missing data.")
            except Exception as e:
                st.error(f"Error loading strategy: {e}")


with col2:
    if selected_strategy != "Select a strategy...":
        if st.button("🗑 Delete Strategy"):
            st.session_state.show_delete_option = True  # Show confirmation checkbox

# Show delete confirmation checkbox only when delete button is pressed
if st.session_state.get("show_delete_option", False):
    confirm_delete = st.checkbox(f"✅ Confirm deletion of '{selected_strategy}'")
    if confirm_delete and st.button("❌ Confirm Delete"):
        delete_strategy(selected_strategy)
        st.success(f"✅ '{selected_strategy}' has been deleted!")
        st.session_state.loaded_strategy = None  # Clear loaded strategy
        st.session_state.show_delete_option = False  # Hide delete confirmation
        time.sleep(3)
        st.rerun()

# Show strategy data in full-width only if loaded
if "loaded_strategy" in st.session_state and st.session_state.loaded_strategy:
    st.session_state.setdefault(
        "loaded_results", {}
    )  # Initializes with an empty dictionary if not already set
    st.session_state.setdefault("loaded_df", None)  # Ensure 'loaded_df' is initialized

    st.markdown(f"## 📌 Loaded Strategy: **{st.session_state.loaded_strategy}**")

    st.subheader("📊 Strategy Parameters")
    st.json(st.session_state.loaded_params)

    st.write(f"Data Path: {st.session_state.ohlcv_path}")

    st.subheader("📈 Backtest Results")
    st.json(st.session_state.loaded_results)

    st.subheader("📉 OHLCV Data Preview")
    if st.session_state.loaded_df is not None:
        st.dataframe(st.session_state.loaded_df)
    else:
        st.warning("No data loaded yet.")
