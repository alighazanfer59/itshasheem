import aiohttp
import asyncio
import pandas as pd
import datetime

# import nest_asyncio

# nest_asyncio.apply()  # Allows asyncio to run inside Jupyter

BASE_URL = "https://api.exchange.coinbase.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_RETRIES = 5  # Number of times to retry on rate limit
RATE_LIMIT_DELAY = 1.5  # Adjust this based on your observations


async def fetch_ohlcv(session, product_id, granularity, start_time, end_time):
    """Asynchronously fetch OHLCV data with retries on 429 errors."""
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
    """Fetch OHLCV data asynchronously with rate limiting."""
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=days)

    tasks = []
    async with aiohttp.ClientSession() as session:
        while start_time < end_time:
            next_end_time = start_time + datetime.timedelta(seconds=granularity * 300)

            # Create async task for each request
            tasks.append(
                fetch_ohlcv(session, product_id, granularity, start_time, next_end_time)
            )

            # Move start time forward
            start_time = next_end_time

            # Apply rate limiting
            await asyncio.sleep(RATE_LIMIT_DELAY)

        # Run all requests concurrently
        results = await asyncio.gather(*tasks)

    # Flatten results (remove None values)
    all_candles = [candle for result in results if result for candle in result]
    return all_candles


def format_ohlcv_data(raw_candles):
    """Format raw OHLCV data into a Pandas DataFrame."""
    if not raw_candles:
        print("No data available.")
        return None

    df = pd.DataFrame(
        raw_candles, columns=["time", "low", "high", "open", "close", "volume"]
    )
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)
    df = df.sort_index(ascending=True)
    df = df.astype(float)
    df = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    return df


# # Run the async function
# raw_ohlcv_data = asyncio.run(
#     fetch_all_historical_ohlcv(product_id, granularity, num_days)
# )

# Format DataFrame
# df = format_ohlcv_data(raw_ohlcv_data)

# # Print first 5 rows
# print(df.head())
