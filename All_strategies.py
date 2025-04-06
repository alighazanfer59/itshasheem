import pandas as pd
import ta
from backtesting import Strategy
from backtesting.lib import crossover
from logger import get_logger

# Get module-specific logger
logger = get_logger(__name__)
logger.info(f"Running module: {__name__}")


# Base Strategy Class with User Parameters
class BaseStrategy(Strategy):
    def init(self):
        try:
            self.params = getattr(self, "strategy_params", {})
            logger.info(
                f"[{self.__class__.__name__}] Strategy Parameters: {self.params}"
            )

            # Log DataFrame columns and head
            if isinstance(self.data.df, pd.DataFrame):
                logger.info(
                    f"[{self.__class__.__name__}] Data Columns: {self.data.df.columns.tolist()}"
                )
                logger.info(
                    f"[{self.__class__.__name__}] Data Sample:\n{self.data.df.head()}"
                )
            else:
                logger.warning(
                    f"[{self.__class__.__name__}] self.data.df is not a DataFrame"
                )

            self.trade_mode = self.params.get("trade_mode", "both").lower()
        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error during init: {e}")

    def can_trade_long(self):
        return self.trade_mode in ["both", "long"]

    def can_trade_short(self):
        return self.trade_mode in ["both", "short"]

    def calculate_trade_size(self):
        try:
            position_size = self.params.get("position_size", 0.99) / 100
            return min(max(position_size, 0.01), 1)
        except Exception as e:
            logger.exception(
                f"[{self.__class__.__name__}] Error calculating trade size: {e}"
            )
            return 0.01  # fallback to minimum


# === Strategy 1 ===
class BollingerRSIReversal(BaseStrategy):
    def init(self):
        try:
            super().init()
            close = self.data.Close
            indicators = self.params.get("indicators", {})

            self.bb_length = indicators.get("bb_length", 20)
            self.bb_std = indicators.get("bb_std", 2)
            self.rsi_length = indicators.get("rsi_length", 14)
            self.rsi_overbought = indicators.get("rsi_overbought", 75)
            self.rsi_oversold = indicators.get("rsi_oversold", 25)

            self.bb_lower = self.I(
                lambda x: ta.volatility.bollinger_lband(
                    pd.Series(x), self.bb_length, self.bb_std
                ),
                close,
            )
            self.bb_upper = self.I(
                lambda x: ta.volatility.bollinger_hband(
                    pd.Series(x), self.bb_length, self.bb_std
                ),
                close,
            )
            self.rsi = self.I(
                lambda x: ta.momentum.rsi(pd.Series(x), self.rsi_length), close
            )

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error during init: {e}")

    def next(self):
        try:
            current_price = self.data.Close[-1]

            if self.position:
                entry_price = self.trades[-1].entry_price if self.trades else None
                if entry_price:
                    if (
                        self.position.is_long
                        and current_price > self.bb_upper[-1]
                        and self.rsi[-1] > self.rsi_overbought
                    ):
                        self.position.close()
                    elif (
                        self.position.is_short
                        and current_price < self.bb_lower[-1]
                        and self.rsi[-1] < self.rsi_oversold
                    ):
                        self.position.close()

            if not self.position:
                if (
                    self.can_trade_long()
                    and self.rsi[-1] < self.rsi_oversold
                    and current_price < self.bb_lower[-1]
                ):
                    self.buy(size=self.calculate_trade_size(), tag="Long Entry")

                elif (
                    self.can_trade_short()
                    and self.rsi[-1] > self.rsi_overbought
                    and current_price > self.bb_upper[-1]
                ):
                    self.sell(size=self.calculate_trade_size(), tag="Short Entry")

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error in next(): {e}")


# === Strategy 2 ===
class RSIBreakoutMomentum(BaseStrategy):
    def init(self):
        try:
            super().init()
            close = self.data.Close
            indicators = self.params.get("indicators", {})

            self.bb_length = indicators.get("bb_length", 20)
            self.bb_std = indicators.get("bb_std", 2)
            self.rsi_length = indicators.get("rsi_length", 14)
            self.rsi_overbought = indicators.get("rsi_overbought", 75)
            self.rsi_oversold = indicators.get("rsi_oversold", 25)
            self.adx_length = indicators.get("adx_length", 14)
            self.adx_threshold = indicators.get("adx_threshold", 30)
            self.take_profit_pct = indicators.get("take_profit_pct", 5) / 100
            self.stop_loss_pct = indicators.get("stop_loss_pct", 5) / 100

            self.bb_upper = self.I(
                lambda x: ta.volatility.bollinger_hband(
                    pd.Series(x), self.bb_length, self.bb_std
                ),
                close,
            )
            self.rsi = self.I(
                lambda x: ta.momentum.rsi(pd.Series(x), self.rsi_length), close
            )
            self.adx = self.I(
                lambda x: ta.trend.adx(
                    pd.Series(self.data.High),
                    pd.Series(self.data.Low),
                    pd.Series(self.data.Close),
                    self.adx_length,
                ),
                close,
            )

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error during init: {e}")

    def next(self):
        try:
            current_price = self.data.Close[-1]

            if self.position:
                entry_price = self.trades[-1].entry_price if self.trades else None
                if entry_price:
                    if self.position.is_long and (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                    elif self.position.is_short and (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

            if not self.position:
                if (
                    self.can_trade_long()
                    and self.rsi[-1] > self.rsi_overbought
                    and current_price > self.bb_upper[-1]
                ):
                    self.buy(size=self.calculate_trade_size(), tag="Long Entry")

                elif (
                    self.can_trade_short()
                    and self.rsi[-1] < self.rsi_oversold
                    and self.adx[-1] > self.adx_threshold
                ):
                    self.sell(size=self.calculate_trade_size(), tag="Short Entry")

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error in next(): {e}")


# === Strategy 3 ===
class MACDBollingerMomentum(BaseStrategy):
    def init(self):
        try:
            super().init()
            close = self.data.Close
            indicators = self.params.get("indicators", {})
            macd_fast = indicators.get("macd_fast", 12)
            macd_slow = indicators.get("macd_slow", 26)
            macd_signal = indicators.get("macd_signal", 9)
            bb_length = indicators.get("bb_length", 20)
            bb_std = indicators.get("bb_std", 2)

            self.macd = self.I(
                lambda x: ta.trend.macd(
                    pd.Series(x), macd_fast, macd_slow, macd_signal
                ),
                close,
            )
            self.bb_width = self.I(
                lambda x: ta.volatility.bollinger_wband(
                    pd.Series(x), bb_length, bb_std
                ),
                close,
            )

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error during init: {e}")

    def next(self):
        try:
            current_price = self.data.Close[-1]
            indicators = self.params.get("indicators", {})
            take_profit_pct = indicators.get("take_profit_pct", 5) / 100
            stop_loss_pct = indicators.get("stop_loss_pct", 5) / 100

            if self.position:
                entry_price = self.trades[-1].entry_price if self.trades else None
                if entry_price:
                    if self.position.is_long and (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                    elif self.position.is_short and (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

            if not self.position:
                if (
                    self.can_trade_long()
                    and crossover(self.macd, 0)
                    and self.bb_width[-1] > 0
                ):
                    self.buy(size=self.calculate_trade_size(), tag="Long Entry")

                elif (
                    self.can_trade_short()
                    and crossover(0, self.macd)
                    and self.bb_width[-1] > 0
                ):
                    self.sell(size=self.calculate_trade_size(), tag="Short Entry")

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error in next(): {e}")


# === Strategy 4 ===
class MovingAverageTrend(BaseStrategy):
    def init(self):
        try:
            super().init()
            close = self.data.Close
            indicators = self.params.get("indicators", {})
            ma_length = indicators.get("ma_length", 200)
            rsi_length = indicators.get("rsi_length", 14)
            self.rsi_threshold = indicators.get("rsi_threshold", 50)

            self.sma_200 = self.I(
                lambda x: ta.trend.sma_indicator(pd.Series(x), ma_length), close
            )
            self.rsi = self.I(
                lambda x: ta.momentum.rsi(pd.Series(x), rsi_length), close
            )

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error during init: {e}")

    def next(self):
        try:
            current_price = self.data.Close[-1]
            indicators = self.params.get("indicators", {})
            take_profit_pct = indicators.get("take_profit_pct", 5) / 100
            stop_loss_pct = indicators.get("stop_loss_pct", 5) / 100

            if self.position:
                entry_price = self.trades[-1].entry_price if self.trades else None
                if entry_price:
                    if self.position.is_long and (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                    elif self.position.is_short and (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

            if not self.position:
                if (
                    self.can_trade_long()
                    and self.rsi[-1] > self.rsi_threshold
                    and current_price > self.sma_200[-1]
                ):
                    self.buy(size=self.calculate_trade_size(), tag="Long Entry")

                elif (
                    self.can_trade_short()
                    and self.rsi[-1] < self.rsi_threshold
                    and current_price < self.sma_200[-1]
                ):
                    self.sell(size=self.calculate_trade_size(), tag="Short Entry")

        except Exception as e:
            logger.exception(f"[{self.__class__.__name__}] Error in next(): {e}")
