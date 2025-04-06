import pandas as pd
import streamlit as st
from logger import get_logger
from pathlib import Path
import importlib
import json

from backtesting import Backtest

# from All_strategies import (
#     BollingerRSIReversal,
#     RSIBreakoutMomentum,
#     MACDBollingerMomentum,
#     MovingAverageTrend,
# )

# Get module-specific logger
logger = get_logger(__name__)
# log module name
logger.info(f"Running module: {__name__}")


# Load strategy registry
def load_strategy_registry(path="strategy_registry.json"):
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"{path} not found. Please add your strategies there.")

    with open(registry_path, "r") as f:
        raw_mapping = json.load(f)

    strategy_classes = {}
    for strategy_name, full_class_path in raw_mapping.items():
        module_name, class_name = full_class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        strategy_class = getattr(module, class_name)
        strategy_classes[strategy_name] = strategy_class

    return strategy_classes


STRATEGY_CLASSES = load_strategy_registry()
logger.info(f"Loaded strategy classes: {list(STRATEGY_CLASSES.keys())}")
# # Mapping strategy names to classes
# STRATEGY_CLASSES = {
#     "Strategy 1": BollingerRSIReversal,
#     "Strategy 2": RSIBreakoutMomentum,
#     "Strategy 3": MACDBollingerMomentum,
#     "Strategy 4": MovingAverageTrend,
# }


def is_running_in_jupyter():
    """Detect if running in a Jupyter Notebook."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except:
        return False


def run_backtest(df, strategy_name, strategy_config):
    """Runs a backtest for the given strategy with the provided parameters."""
    StrategyClass = STRATEGY_CLASSES.get(strategy_name)

    if not StrategyClass:
        msg = f"⚠️ Strategy '{strategy_name}' not found."
        if is_running_in_jupyter():
            print(msg)
        else:
            import streamlit as st

            st.error(msg)
        logger.error(msg)
        return None
    else:
        logger.info(f"Strategy Class Found: {StrategyClass.__name__}")

    # Update strategy parameters as class attributes so Backtest.run() recognizes them
    for param_name, param_value in strategy_config.items():
        logger.info(f"[{strategy_name}] Set parameter {param_name}: {param_value}")

    if hasattr(StrategyClass, "strategy_params"):
        StrategyClass.strategy_params.update(strategy_config)
    else:
        StrategyClass.strategy_params = strategy_config

    logger.info(f"Running backtest for strategy: {strategy_name}")
    logger.info(f"Final Parameters Used: {strategy_config}")

    if is_running_in_jupyter():
        print(f"📊 Running backtest with strategy: {strategy_name}")
        print(f"📌 Strategy parameters: {strategy_config}")

    # Initialize Backtest with configured strategy
    initial_cash = strategy_config.get("initial_cash", 10000)
    commission = strategy_config.get("commission", 0.001)

    bt = Backtest(df, StrategyClass, cash=initial_cash, commission=commission)

    stats = bt.run()  # Pass parameters when calling run()

    # Print results in Jupyter for immediate feedback
    if is_running_in_jupyter():
        print("Backtest Results:", stats)

    return stats
