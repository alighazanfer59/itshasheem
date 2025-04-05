# 📘 Strategy Backtesting Framework

## 🚀 1. Overview

This project allows you to backtest trading strategies using a modular and pluggable approach.  
Strategies are defined in `All_strategies.py`, registered in a simple JSON file, and dynamically imported for testing using Streamlit.

---

## 🧠 2. How to Add a New Strategy

You **do NOT need to modify `backtest.py`** anymore. Just follow the steps below:

### ✅ A. Create Your Strategy in `All_strategies.py`

```python
class MyNewStrategy:
    def __init__(self, df, params):
        self.df = df
        self.params = params

    def generate_signals(self):
        # Your logic to generate buy/sell signals
        self.df["signal"] = 0
        return self.df
```

### ✅ B. Register the Strategy in `strategy_registry.json`

```json
{
  "Strategy 1": "All_strategies.BollingerRSIReversal",
  "Strategy 2": "All_strategies.RSIBreakoutMomentum",
  "Strategy 3": "All_strategies.MACDBollingerMomentum",
  "Strategy 4": "All_strategies.MovingAverageTrend",
  "Strategy 5": "All_strategies.MyNewStrategy"
}
```

📌 Format: `"Strategy Name": "module_name.ClassName"`

### ✅ C. Add Parameters in `str_params.json`

```json
"Strategy 5": {
  "description": "My new strategy using XYZ indicators",
  "indicators": {
    "my_param1": 14,
    "my_param2": 2.0
  }
}
```

---

---

## 🧠 3. How to Add a New Strategy with Custom Indicators (Backtesting.py Style)

This project also supports strategies using the [`backtesting.py`](https://kernc.github.io/backtesting.py/) engine.

Your strategy class must inherit from `Strategy` and implement two key methods:

- **`init()`** – for indicator calculation and initialization.
- **`next()`** – for defining entry and exit logic on every new bar.

---

### ✅ Step 1: Add Strategy Class in `All_strategies.py`

```python
from backtesting import Strategy
import ta  # Technical Analysis library

class MyNewStrategy(Strategy):
    # Parameters must match keys in str_params.json
    strategy_params = {}

    def init(self):
        # Get user-defined params
        rsi_len = self.strategy_params.get("rsi_length", 14)
        bb_len = self.strategy_params.get("bb_length", 20)
        bb_std = self.strategy_params.get("bb_std", 2)

        close = self.data.Close

        self.rsi = self.I(lambda x: ta.momentum.RSIIndicator(x, rsi_len).rsi(), close)
        self.bb_upper = self.I(lambda x: ta.volatility.BollingerBands(x, bb_len, bb_std).bollinger_hband(), close)
        self.bb_lower = self.I(lambda x: ta.volatility.BollingerBands(x, bb_len, bb_std).bollinger_lband(), close)

    def next(self):
        price = self.data.Close[-1]

        if price < self.bb_lower[-1] and self.rsi[-1] < 30:
            self.buy()
        elif price > self.bb_upper[-1] and self.rsi[-1] > 70:
            self.sell()
```

📌 **Notes:**

- Use `strategy_params.get()` to safely pull values defined in `str_params.json`.
- Use `self.I()` to register indicators efficiently with `backtesting.py`.
- Do **not** override `__init__`; use `init()` for setup and `next()` for signals.

---

### ✅ Step 2: Register the Strategy

Update `strategy_registry.json`:

```json
{
  "Strategy 6": "All_strategies.MyNewStrategy"
}
```

---

### ✅ Step 3: Add Parameters to `str_params.json`

```json
"Strategy 6": {
  "description": "My Custom Indicator Strategy using RSI + Bollinger Bands",
  "indicators": {
    "rsi_length": 14,
    "bb_length": 20,
    "bb_std": 2
  }
}
```

---

## ⚙️ 4. How Strategies Are Loaded Dynamically

In `backtest.py`, use the following to dynamically load from the registry:

```python
import importlib
import json
from pathlib import Path

def load_strategy_registry(path="strategy_registry.json"):
    with open(path, "r") as f:
        raw_mapping = json.load(f)

    strategy_classes = {}
    for strategy_name, full_class_path in raw_mapping.items():
        module_name, class_name = full_class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        strategy_class = getattr(module, class_name)
        strategy_classes[strategy_name] = strategy_class

    return strategy_classes

STRATEGY_CLASSES = load_strategy_registry()
```

---

## 🖥️ 5. Running the Application

### ✅ Step 5a: Run the Backtest (via Streamlit or Code)

The main entry point for this Streamlit app is:

```bash
streamlit run Home.py
```

### 📂 Pages Overview

- **Backtest_Strategies.py** – Run backtests using your selected strategy and parameters.
- **Saved_Strategies.py** – View and load previously saved backtested strategies.
- **Compare_Key_Metrices.py** – Compare key performance metrics across multiple strategies.

> Make sure `Home.py` and all pages are in the correct structure for Streamlit to detect and render.

---

From the UI:

- Select **Strategy 6**.
- Enter the custom indicator values (or use defaults).
- Run and review results interactively.

From code:

```python
from backtest import run_backtest
stats = run_backtest(df, "Strategy 6", config)
```

## 💻 6. Virtual Environment Setup

### 🪟 For Windows

```bash
cd your_project_folder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 🍏 For macOS / Linux

```bash
cd your_project_folder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❎ To Deactivate Virtual Environment

```bash
deactivate
```

---

## 🧪 7. Running the Backtest (Functionally)

Backtesting is also supported programmatically via:

```python
from backtest import run_backtest
stats = run_backtest(df, strategy_name, strategy_config)
```

---

## 📦 File Structure Overview

| File/Folder                     | Purpose                                         |
| ------------------------------- | ----------------------------------------------- |
| `All_strategies.py`             | Contains all strategy class definitions         |
| `strategy_registry.json`        | Maps strategy names to classes (dynamic import) |
| `str_params.json`               | Parameter definitions for each strategy         |
| `backtest.py`                   | Runs backtests programmatically                 |
| `Home.py`                       | Main Streamlit entry point                      |
| `pages/Backtest_Strategies.py`  | Streamlit page for backtesting                  |
| `pages/Compare_Key_Metrices.py` | Page to compare performance                     |
| `pages/Saved_Strategies.py`     | View saved strategy results                     |
| `requirements.txt`              | List of required packages                       |
| `venv/`                         | Virtual environment folder (auto-generated)     |

---

## 🆘 Troubleshooting

- ✅ Match the strategy name exactly across all files
- ✅ Ensure JSON files are valid (use an online JSON validator)
- ✅ Activate your virtual environment before running

---

🎉 You're now ready to build, add, backtest, and compare strategies dynamically!
