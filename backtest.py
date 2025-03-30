# import pandas as pd
import streamlit as st
# import sys
from backtesting import Backtest
from All_strategies import (
    BollingerRSIReversal,
    RSIBreakoutMomentum,
    MACDBollingerMomentum,
    MovingAverageTrend,
)

# Mapping strategy names to classes
STRATEGY_CLASSES = {
    "Strategy 1": BollingerRSIReversal,
    "Strategy 2": RSIBreakoutMomentum,
    "Strategy 3": MACDBollingerMomentum,
    "Strategy 4": MovingAverageTrend,
}


def is_running_in_jupyter():
    """Detect if running in a Jupyter Notebook."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except Exception:
        return False


def run_backtest(df, selected_strategy, strategy_config):
    StrategyClass = STRATEGY_CLASSES.get(selected_strategy)

    if not StrategyClass:
        if is_running_in_jupyter():
            print(f"⚠️ Strategy '{selected_strategy}' not found.")
        else:
            st.error(f"⚠️ Strategy '{selected_strategy}' not found.")
        return None

    if hasattr(StrategyClass, "strategy_params"):
        StrategyClass.strategy_params.update(strategy_config)
    else:
        StrategyClass.strategy_params = strategy_config

    if is_running_in_jupyter():
        print(f"📊 Running backtest with strategy: {selected_strategy}")
        print(f"📌 Strategy parameters: {strategy_config}")
    else:
        st.write("📊 Running backtest with strategy:", selected_strategy)
        st.write("📌 Strategy parameters:", strategy_config)

    initial_cash = strategy_config.get("initial_cash", 10000)
    commission = strategy_config.get("commission", 0.0005)

    bt = Backtest(df, StrategyClass, cash=initial_cash, commission=commission)
    results = bt.run()

    return results
