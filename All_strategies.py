# import numpy as np
import pandas as pd
import ta

# import logging
from backtesting import Strategy
from backtesting.lib import crossover

from logger import get_logger  # Import the same logger from logger.py

# Get module-specific logger
logger = get_logger(__name__)
logger.info(f"Running module: {__name__}")


# Base Strategy Class with User Parameters
class BaseStrategy(Strategy):
    def init(self):
        self.params = getattr(self, "strategy_params", {})
        logger.info(
            f"[{self.__class__.__name__}] Backtest BaseStrategy Parameters: {self.params}"
        )

        self.trade_mode = self.params.get(
            "trade_mode", "both"
        ).lower()  # Convert to lowercase

    def can_trade_long(self):
        return self.trade_mode in ["both", "long"]

    def can_trade_short(self):
        return self.trade_mode in ["both", "short"]

    def calculate_trade_size(self):
        position_size = (
            self.params.get("position_size", 0.99) / 100
        )  # Convert % to fraction
        return min(max(position_size, 0.01), 1)  # Ensure it's between 0.01 and 1


class BollingerRSIReversal(BaseStrategy):
    def init(self):
        self.params = getattr(self, "strategy_params", {})  # Ensure params are set
        logger.info(f"[{self.__class__.__name__}] Strategy Parameters: {self.params}")
        super().init()
        close = self.data.Close

        # ✅ Extract indicators safely
        indicators = self.params.get("indicators", {})

        self.bb_length = indicators.get("bb_length", 20)
        self.bb_std = indicators.get("bb_std", 2)  # ✅ Use bb_std from JSON
        self.rsi_length = indicators.get("rsi_length", 14)
        self.rsi_overbought = indicators.get("rsi_overbought", 75)
        self.rsi_oversold = indicators.get("rsi_oversold", 25)

        logger.info(
            f"[{self.__class__.__name__}] RSI Period: {self.rsi_length}, BB Window: {self.bb_length}, BB Std: {self.bb_std}"
        )
        logger.info(
            f"[{self.__class__.__name__}] RSI Overbought: {self.rsi_overbought}, RSI Oversold: {self.rsi_oversold}"
        )

        # ✅ Corrected Bollinger Band calculations to include std deviation
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

    def next(self):
        current_price = self.data.Close[-1]

        # ✅ Close existing trades with dynamic TP & SL
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            if entry_price:
                if self.position.is_long:
                    if (
                        current_price > self.bb_upper[-1]
                        and self.rsi[-1] > self.rsi_overbought
                    ):
                        self.position.close()
                elif self.position.is_short:
                    if (
                        current_price < self.bb_lower[-1]
                        and self.rsi[-1] < self.rsi_oversold
                    ):
                        self.position.close()

        # ✅ Entry conditions now fully use configurable parameters
        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] < self.rsi_oversold
            and current_price < self.bb_lower[-1]
        ):
            self.buy(size=self.calculate_trade_size(), tag="Long Entry")

        elif (
            self.can_trade_short()
            and self.rsi[-1] > self.rsi_overbought
            and current_price > self.bb_upper[-1]
            and not self.position
        ):
            self.sell(size=self.calculate_trade_size(), tag="Short Entry")


# Strategy 2: RSI Overbought & BB Breakout
class RSIBreakoutMomentum(BaseStrategy):
    def init(self):
        self.params = getattr(self, "strategy_params", {})  # Ensure params are set
        super().init()
        close = self.data.Close

        # ✅ Extract indicators safely
        indicators = self.params.get("indicators", {})

        self.bb_length = indicators.get("bb_length", 20)
        self.bb_std = indicators.get("bb_std", 2)
        self.rsi_length = indicators.get("rsi_length", 14)
        self.rsi_overbought = indicators.get("rsi_overbought", 75)
        self.rsi_oversold = indicators.get("rsi_oversold", 25)
        self.adx_length = indicators.get("adx_length", 14)
        self.adx_threshold = indicators.get("adx_threshold", 30)
        self.take_profit_pct = indicators.get("take_profit_pct", 0.05) / 100
        self.stop_loss_pct = indicators.get("stop_loss_pct", 0.05) / 100

        logger.info(
            f"[{self.__class__.__name__}] Take Profit: {self.take_profit_pct}, Stop Loss: {self.stop_loss_pct}"
        )
        # ✅ Calculate indicators dynamically
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

    def next(self):
        current_price = self.data.Close[-1]

        # ✅ Close existing trades with dynamic TP & SL
        # if self.position:
        #     # entry_price = self.trades[-1].entry_price if self.trades else None
        #     for trade in self.trades:
        #         entry_price = trade.entry_price  # Get the entry price for each trade

        #         if entry_price:  # Ensure entry_price is not None

        #             if trade.is_long:
        #                 trade.sl = entry_price * (
        #                     1 - self.stop_loss_pct
        #                 )  # Convert to decimal
        #                 trade.tp = entry_price * (1 + self.take_profit_pct)
        #             else:
        #                 trade.sl = entry_price * (1 + self.stop_loss_pct)
        #                 trade.tp = entry_price * (1 - self.take_profit_pct)
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            if entry_price:
                if self.position.is_long:
                    if (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                elif self.position.is_short:
                    if (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

        # ✅ Entry conditions using dynamic parameters
        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] > self.rsi_overbought
            and current_price > self.bb_upper[-1]
        ):
            self.buy(size=self.calculate_trade_size(), tag="Long Entry")

        elif (
            not self.position
            and self.can_trade_short()
            and self.rsi[-1] < self.rsi_oversold
            and self.adx[-1] > self.adx_threshold
        ):
            self.sell(size=self.calculate_trade_size(), tag="Short Entry")


# Strategy 3: MACD Crossover & BB Width
class MACDBollingerMomentum(BaseStrategy):
    def init(self):
        self.params = getattr(self, "strategy_params", {})
        super().init()
        close = self.data.Close

        # ✅ Extract indicator parameters from user-defined JSON
        indicators = self.params.get("indicators", {})
        macd_fast = indicators.get("macd_fast", 12)
        macd_slow = indicators.get("macd_slow", 26)
        macd_signal = indicators.get("macd_signal", 9)
        bb_length = indicators.get("bb_length", 20)
        bb_std = indicators.get("bb_std", 2)

        # ✅ MACD Calculation
        self.macd = self.I(
            lambda x: ta.trend.macd(pd.Series(x), macd_fast, macd_slow, macd_signal),
            close,
        )

        # ✅ Bollinger Band Width Calculation with `bb_std`
        self.bb_width = self.I(
            lambda x: ta.volatility.bollinger_wband(pd.Series(x), bb_length, bb_std),
            close,
        )

    def next(self):
        current_price = self.data.Close[-1]

        # ✅ Extract trade parameters
        indicators = self.params.get("indicators", {})
        take_profit_pct = indicators.get("take_profit_pct", 0.05) / 100
        stop_loss_pct = indicators.get("stop_loss_pct", 0.05) / 100
        # ✅ Log the parameters
        logger.info(
            f"[{self.__class__.__name__}] Take Profit: {take_profit_pct}, Stop Loss: {stop_loss_pct}"
        )
        # ✅ Close existing trades with dynamic TP & SL
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            # for trade in self.trades:
            #     entry_price = trade.entry_price  #   Get the entry price for each trade
            #     if entry_price:  # Ensure entry_price is not None
            #         if trade.is_long:
            #             trade.sl = entry_price * (1 - stop_loss_pct)
            #             trade.tp = entry_price * (1 + take_profit_pct)
            #         else:
            #             trade.sl = entry_price * (1 + stop_loss_pct)
            #             trade.tp = entry_price * (1 - take_profit_pct)
            if entry_price:
                if self.position.is_long:
                    if (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                elif self.position.is_short:
                    if (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

        # ✅ Entry conditions using dynamic parameters
        if (
            not self.position
            and self.can_trade_long()
            and crossover(self.macd, 0)
            and self.bb_width[-1] > 0
        ):
            self.buy(
                size=self.calculate_trade_size(),
                tag="Long Entry",
            )

        elif (
            not self.position
            and self.can_trade_short()
            and crossover(0, self.macd)
            and self.bb_width[-1] > 0
        ):
            self.sell(
                size=self.calculate_trade_size(),
                tag="Short Entry",
            )


class MovingAverageTrend(BaseStrategy):
    def init(self):
        self.params = getattr(self, "strategy_params", {})
        super().init()
        close = self.data.Close

        # ✅ Extract indicator parameters from JSON
        indicators = self.params.get("indicators", {})
        ma_length = indicators.get("ma_length", 200)  # Renamed for consistency
        rsi_length = indicators.get("rsi_length", 14)
        self.rsi_threshold = indicators.get("rsi_threshold", 50)

        # ✅ Moving Average & RSI Calculation
        self.sma_200 = self.I(
            lambda x: ta.trend.sma_indicator(pd.Series(x), ma_length), close
        )
        self.rsi = self.I(lambda x: ta.momentum.rsi(pd.Series(x), rsi_length), close)

    def next(self):
        current_price = self.data.Close[-1]

        # ✅ Extract trade parameters
        indicators = self.params.get("indicators", {})
        take_profit_pct = indicators.get("take_profit_pct", 0.05) / 100
        stop_loss_pct = indicators.get("stop_loss_pct", 0.05) / 100
        # ✅ Log the parameters
        logger.info(
            f"[{self.__class__.__name__}] Take Profit: {take_profit_pct}, Stop Loss: {stop_loss_pct}"
        )

        # ✅ Close existing trades with dynamic TP & SL
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            # for trade in self.trades:
            #     entry_price = trade.entry_price  # Get the entry price for each trade
            #     if entry_price:  # Ensure entry_price is not None
            #         if trade.is_long:
            #             trade.sl = entry_price * (1 - stop_loss_pct)
            #             trade.tp = entry_price * (1 + take_profit_pct)
            #         else:
            #             trade.sl = entry_price * (1 + stop_loss_pct)
            #             trade.tp = entry_price * (1 - take_profit_pct)
            if entry_price:
                if self.position.is_long:
                    if (
                        current_price >= entry_price * 1.05
                        or current_price <= entry_price * 0.95
                    ):
                        self.position.close()
                elif self.position.is_short:
                    if (
                        current_price <= entry_price * 0.95
                        or current_price >= entry_price * 1.05
                    ):
                        self.position.close()

        # ✅ Entry conditions using dynamic parameters
        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] > self.rsi_threshold
            and current_price > self.sma_200[-1]
        ):
            self.buy(size=self.calculate_trade_size(), tag="Long Entry")

        elif (
            not self.position
            and self.can_trade_short()
            and self.rsi[-1] < self.rsi_threshold
            and current_price < self.sma_200[-1]
        ):
            self.sell(size=self.calculate_trade_size(), tag="Short Entry")
