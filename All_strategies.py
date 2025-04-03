# import numpy as np
import pandas as pd
import ta
# import logging
from backtesting import Strategy
from backtesting.lib import crossover


# Base Strategy Class with User Parameters
class BaseStrategy(Strategy):
    def init(self):
        self.params = self.strategy_params  # User-defined params
        self.trade_mode = self.params.get("trade_mode", "both")  # Default to both

    def can_trade_long(self):
        return self.trade_mode in ["both", "long"]

    def can_trade_short(self):
        return self.trade_mode in ["both", "short"]

    def calculate_trade_size(self):
        return self.params.get("trade_size", 0.99)  # Default to 0.99 if not provided


# Strategy 1: BB & RSI Extreme Reversal
class BollingerRSIReversal(BaseStrategy):
    def init(self):
        super().init()
        close = self.data.Close

        bb_length = self.params.get("bb_length", 20)
        rsi_length = self.params.get("rsi_length", 14)

        self.bb_lower = self.I(
            lambda x: ta.volatility.bollinger_lband(pd.Series(x), bb_length), close
        )
        self.bb_upper = self.I(
            lambda x: ta.volatility.bollinger_hband(pd.Series(x), bb_length), close
        )
        self.rsi = self.I(lambda x: ta.momentum.rsi(pd.Series(x), rsi_length), close)

    def next(self):
        current_price = self.data.Close[-1]
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            if entry_price:
                if self.position.is_long:
                    if (
                        current_price > self.bb_upper[-1]
                        and self.rsi[-1] > 75
                    ):
                        self.position.close()
                elif self.position.is_short:
                    if (
                        current_price < self.bb_lower[-1]
                        and self.rsi[-1] < 25
                    ):
                        self.position.close()

        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] < 25
            and current_price < self.bb_lower[-1]
        ):
            self.buy(size=self.calculate_trade_size(), tag="Long Entry")

        elif (
            self.can_trade_short()
            and self.rsi[-1] > 75
            and current_price > self.bb_upper[-1]
            and not self.position
        ):
            self.sell(size=self.calculate_trade_size(), tag="Short Entry")


# Strategy 2: RSI Overbought & BB Breakout
class RSIBreakoutMomentum(BaseStrategy):
    def init(self):
        super().init()
        close = self.data.Close

        bb_length = self.params.get("bb_length", 20)
        rsi_length = self.params.get("rsi_length", 14)
        adx_length = self.params.get("adx_length", 14)

        self.bb_upper = self.I(
            lambda x: ta.volatility.bollinger_hband(pd.Series(x), bb_length), close
        )
        self.rsi = self.I(lambda x: ta.momentum.rsi(pd.Series(x), rsi_length), close)
        self.adx = self.I(
            lambda x: ta.trend.adx(
                pd.Series(self.data.High),
                pd.Series(self.data.Low),
                pd.Series(self.data.Close),
                adx_length,
            ),
            close,
        )

    def next(self):
        current_price = self.data.Close[-1]
        # if self.position:
        #     entry_price = self.trades[-1].entry_price if self.trades else None
            
        #     for trade in self.trades:
        #         if trade.is_long:
        #             trade.sl = entry_price * 0.95
        #             trade.tp = entry_price * 1.05
        #         else:
        #             trade.sl = entry_price * 1.05
        #             trade.tp = entry_price * 0.95
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

        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] > 75
            and current_price > self.bb_upper[-1]
        ):
            self.buy(size=self.calculate_trade_size(), tag="Long Entry")

        elif not self.position and self.can_trade_short() and self.rsi[-1] < 75 and self.adx[-1] > 30:
            self.sell(size=self.calculate_trade_size(), tag="Short Entry")


# Strategy 3: MACD Crossover & BB Width
class MACDBollingerMomentum(BaseStrategy):
    def init(self):
        super().init()
        close = self.data.Close

        macd_fast = self.params.get("macd_fast", 12)
        macd_slow = self.params.get("macd_slow", 26)
        macd_signal = self.params.get("macd_signal", 9)
        bb_length = self.params.get("bb_length", 20)

        self.macd = self.I(
            lambda x: ta.trend.macd(pd.Series(x), macd_fast, macd_slow, macd_signal),
            close,
        )
        self.bb_width = self.I(
            lambda x: ta.volatility.bollinger_wband(pd.Series(x), bb_length), close
        )

    def next(self):
        current_price = self.data.Close[-1]
        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            
            # for trade in self.trades:
            #     if trade.is_long:
            #         trade.sl = entry_price * 0.95
            #         trade.tp = entry_price * 1.05
            #     else:
            #         trade.sl = entry_price * 1.05
            #         trade.tp = entry_price * 0.95
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

        if not self.position and self.can_trade_long() and crossover(self.macd, 0) and self.bb_width[-1] > 0:
            self.buy(size=self.calculate_trade_size(), sl = (current_price * 0.95), tp = (current_price * 1.05))

        elif (
            not self.position and self.can_trade_short() and crossover(0, self.macd) and self.bb_width[-1] > 0
        ):
            self.sell(size=self.calculate_trade_size(), sl = (current_price * 1.05), tp = (current_price * 0.95))


# Strategy 4: 200MA & RSI Trend Following
class MovingAverageTrend(BaseStrategy):
    def init(self):
        super().init()
        close = self.data.Close

        ma_length = self.params.get("ma_length", 200)
        rsi_length = self.params.get("rsi_length", 14)

        self.sma_200 = self.I(
            lambda x: ta.trend.sma_indicator(pd.Series(x), ma_length), close
        )
        self.rsi = self.I(lambda x: ta.momentum.rsi(pd.Series(x), rsi_length), close)

    def next(self):
        current_price = self.data.Close[-1]

        if self.position:
            entry_price = self.trades[-1].entry_price if self.trades else None
            
            # for trade in self.trades:
            #     if trade.is_long:
            #         trade.sl = entry_price * 0.95
            #         trade.tp = entry_price * 1.05
            #     else:
            #         trade.sl = entry_price * 1.05
            #         trade.tp = entry_price * 0.95
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

        if (
            not self.position
            and self.can_trade_long()
            and self.rsi[-1] > 50
            and current_price > self.sma_200[-1]
        ):
            self.buy(size=self.calculate_trade_size())#, sl = (current_price * 0.95), tp = (current_price * 1.05))

        elif (
            not self.position
            and self.can_trade_short()
            and self.rsi[-1] < 50
            and current_price < self.sma_200[-1]
        ):
            self.sell(size=self.calculate_trade_size())#, sl = (current_price * 1.05), tp = (current_price * 0.95))
