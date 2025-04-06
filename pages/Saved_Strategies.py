import streamlit as st
from strategy_storage import fetch_all_strategies, load_strategy, delete_strategy
import time
from theme_manager import THEMES, apply_theme

# Set page config
st.set_page_config(page_title="Saved Strategies", page_icon="📁", layout="wide")

# ✅ Apply theme from session state
if "selected_theme" in st.session_state:
    apply_theme(THEMES[st.session_state.selected_theme])

st.title("📂 View Saved Strategies")

# Initialize session state safely
for key in [
    "loaded_strategy",
    "loaded_params",
    "loaded_df",
    "loaded_results",
    "ohlcv_path",
    "show_delete_option",
    "last_selected_strategy",
]:
    if key not in st.session_state:
        st.session_state[key] = None

# Fetch saved strategies
strategies = fetch_all_strategies()

if not strategies:
    st.warning("No strategies saved yet!")
    st.stop()

# Add placeholder option
strategy_options = ["Select a strategy..."] + strategies
selected_strategy = st.selectbox("🔍 Select Strategy", strategy_options, index=0)

# Reset delete confirmation if strategy selection changes
if selected_strategy != st.session_state.get("last_selected_strategy"):
    st.session_state["show_delete_option"] = False
    st.session_state["last_selected_strategy"] = selected_strategy

# Buttons in columns
col1, col2 = st.columns([1, 1])

# Load Strategy
with col1:
    if selected_strategy != "Select a strategy...":
        if st.button("📤 Load Strategy"):
            try:
                params, ohlcv_path, df, results = load_strategy(selected_strategy)

                if params and df is not None and results:
                    st.session_state["loaded_strategy"] = selected_strategy
                    st.session_state["loaded_params"] = params
                    st.session_state["ohlcv_path"] = ohlcv_path
                    st.session_state["loaded_df"] = df
                    st.session_state["loaded_results"] = results
                    st.session_state["show_delete_option"] = False
                else:
                    st.error("Failed to load strategy. Missing data.")
            except Exception as e:
                st.error(f"Error loading strategy: {e}")

# Delete Strategy
with col2:
    if selected_strategy != "Select a strategy...":
        if st.button("🗑 Delete Strategy"):
            st.session_state["show_delete_option"] = True

# Confirm Deletion
if st.session_state.get("show_delete_option"):
    with st.form("delete_confirmation_form"):
        confirm_delete = st.checkbox(f"✅ Confirm deletion of '{selected_strategy}'")
        delete_submit = st.form_submit_button("❌ Confirm Delete")

        if confirm_delete and delete_submit:
            try:
                delete_strategy(selected_strategy)
                st.success(f"✅ '{selected_strategy}' has been deleted!")
                time.sleep(2)
                # Reset state
                for key in [
                    "loaded_strategy",
                    "loaded_params",
                    "loaded_df",
                    "loaded_results",
                    "ohlcv_path",
                ]:
                    st.session_state[key] = None
                st.session_state["show_delete_option"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete strategy: {e}")

# Show loaded strategy details
if st.session_state.get("loaded_strategy"):
    st.markdown(f"## 📌 Loaded Strategy: **{st.session_state['loaded_strategy']}**")

    st.subheader("📊 Strategy Parameters")
    st.json(st.session_state.get("loaded_params"))

    st.write(f"**📁 Data Path:** `{st.session_state.get('ohlcv_path')}`")

    st.subheader("📈 Backtest Results")
    st.json(st.session_state.get("loaded_results"))

    st.subheader("📉 OHLCV Data Preview")
    if st.session_state.get("loaded_df") is not None:
        st.dataframe(st.session_state["loaded_df"])
    else:
        st.warning("No data loaded.")
