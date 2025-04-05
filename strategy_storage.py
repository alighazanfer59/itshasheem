import sqlite3
import os
import json
import pandas as pd

db_file = "backtest_strategies.db"
if not os.path.exists("ohlcv_data"):  # Create folder to store OHLCV CSVs
    os.makedirs("ohlcv_data")


def init_db():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT UNIQUE,
                params TEXT,
                ohlcv_path TEXT,
                results TEXT
            )
            """
        )
        conn.commit()


def save_strategy(strategy_name, params, df, results):
    """
    Save strategy parameters, OHLCV data, and backtest results to SQLite.
    """
    ohlcv_path = f"ohlcv_data/{strategy_name}.csv"
    df.to_csv(ohlcv_path, index=True)

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO strategies (strategy_name, params, ohlcv_path, results)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(strategy_name) DO UPDATE SET
                params=excluded.params,
                ohlcv_path=excluded.ohlcv_path,
                results=excluded.results
            """,
            (strategy_name, json.dumps(params), ohlcv_path, json.dumps(results)),
        )
        conn.commit()


def fetch_all_strategies():
    """
    Fetch all saved strategies.
    """
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT strategy_name FROM strategies")
        return [row[0] for row in cursor.fetchall()]


def load_strategy(strategy_name):
    """
    Load strategy parameters and OHLCV data.
    """
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT params, ohlcv_path, results FROM strategies WHERE strategy_name = ?",
            (strategy_name,),
        )
        row = cursor.fetchone()

        if row:
            params = json.loads(row[0])  # Strategy parameters
            ohlcv_path = row[1]  # Correct OHLCV path
            df = pd.read_csv(ohlcv_path, index_col=0, parse_dates=True)  # Load CSV
            results = json.loads(row[2])  # Backtest results
            return params, ohlcv_path, df, results  # Return path separately

        return None, None, None, None  # Ensure correct return values


def delete_strategy(strategy_name):
    """
    Delete a saved strategy and its OHLCV CSV file.
    """
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ohlcv_path FROM strategies WHERE strategy_name = ?",
            (strategy_name,),
        )
        row = cursor.fetchone()

        if row and os.path.exists(row[0]):
            os.remove(row[0])  # Delete the OHLCV CSV file

        cursor.execute(
            "DELETE FROM strategies WHERE strategy_name = ?", (strategy_name,)
        )
        conn.commit()


init_db()
