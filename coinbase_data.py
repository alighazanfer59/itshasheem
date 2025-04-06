# coinbase_data.py
# This script fetches historical OHLCV data from Coinbase Pro API and formats it into a Pandas DataFrame.

import aiohttp
import asyncio
import pandas as pd
import datetime

BASE_URL = "https://api.exchange.coinbase.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_RETRIES = 5
RATE_LIMIT_DELAY = 1.5


async def fetch_ohlcv(session, product_id, granularity, start_time, end_time):
    url = f"{BASE_URL}/products/{product_id}/candles"
    params = {
        "granularity": granularity,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
    }

    retries = 0
    while retries < MAX_RETRIES:
        try:
            async with session.get(url, headers=HEADERS, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    retry_after = response.headers.get("Retry-After", RATE_LIMIT_DELAY)
                    print(f"Rate limited! Retrying in {retry_after} seconds...")
                    await asyncio.sleep(float(retry_after))
                    retries += 1
                else:
                    print(f"Error {response.status}: {await response.text()}")
                    return []
        except aiohttp.ClientError as e:
            print(f"Client error occurred: {e}")
            retries += 1
            await asyncio.sleep(RATE_LIMIT_DELAY)
        except asyncio.TimeoutError:
            print("Request timed out. Retrying...")
            retries += 1
            await asyncio.sleep(RATE_LIMIT_DELAY)
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            return []

    print("Max retries reached. Skipping this batch.")
    return []


async def fetch_all_historical_ohlcv(product_id, granularity, days):
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=days)

    tasks = []
    async with aiohttp.ClientSession() as session:
        while start_time < end_time:
            next_end_time = start_time + datetime.timedelta(seconds=granularity * 300)

            tasks.append(
                fetch_ohlcv(session, product_id, granularity, start_time, next_end_time)
            )

            start_time = next_end_time
            await asyncio.sleep(RATE_LIMIT_DELAY)

        results = await asyncio.gather(*tasks)

    all_candles = [candle for result in results if result for candle in result]
    return all_candles


def format_ohlcv_data(raw_candles):
    if not raw_candles:
        print("No data available.")
        return None

    df = pd.DataFrame(
        raw_candles, columns=["time", "low", "high", "open", "close", "volume"]
    )

    # Convert timestamp to datetime
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["Date"] = df["time"]  # Optional: if 'Date' is needed separately
    df.set_index("time", inplace=True)
    df = df.sort_index()

    # Convert only the numeric columns to float (not datetime)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rename for consistency
    df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        },
        inplace=True,
    )

    # Reorder columns
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    return df
