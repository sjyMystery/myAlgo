from .base import BaseStrategy
from ..broker import BackTestBroker
from ..broker.commission import Commission
from ..feed.barfeed import BaseBarFeed
from ..stratanalyzer.drawdown import DrawDown
from ..stratanalyzer.returns import Returns
from ..stratanalyzer.sharpe import SharpeRatio
from ..stratanalyzer.trades import Trades

"""
This class mainly used to test some strategy.
One should provide the params and then it would save the result into the database.

The strategy should recv the id of params , which would be used to save the result into the database. 

"""


class BackTestStrategy(BaseStrategy):
    name = 'BackTestStrategy'

    def onBars(self, datetime, bars):
        return NotImplementedError()

    def __init__(self, feed: BaseBarFeed, cash: float, commission: Commission, round):
        self.__start_cash = cash
        self.__broker = BackTestBroker(cash, feed, commission=commission, round_quantity=round)

        super(BackTestStrategy, self).__init__(self.__broker)

        self.__analyzers = {
            "ret": Returns(),
            "sharpe": SharpeRatio(),
            "dd": DrawDown(),
            "trades": Trades()
        }

        self.attachAnalyzer(self.__analyzers["ret"])
        self.attachAnalyzer(self.__analyzers["sharpe"])
        self.attachAnalyzer(self.__analyzers["dd"])
        self.attachAnalyzer(self.__analyzers["trades"])

        self.__effects = None

    @property
    def analyzers(self):
        return self.__analyzers

    def calculate_effects(self):

        if self.analyzers["trades"].getCount() == 0:
            self.__effects = None
            return {
                "profit_rate": self.broker.equity / self.__start_cash,
            }

        profits = self.analyzers["trades"].getProfits()
        losses = self.analyzers["trades"].getLosses()
        if len(profits) is 0:
            plr = 0
        elif len(losses) > 0 and losses.mean() != 0:
            plr = profits.mean() / abs(losses.mean())
        else:
            plr = None

        win_rate = self.analyzers["trades"].getProfitableCount() / self.analyzers["trades"].getCount() * 100 \
            if self.analyzers["trades"].getCount() != 0 else None

        self.__effects = {
            "profit_rate": self.broker.equity / self.__start_cash,
            "ret": self.analyzers["ret"].getCumulativeReturns()[-1] * 100,
            "sharp": self.analyzers["sharpe"].getSharpeRatio(0.00),
            "dd": self.analyzers["dd"].getMaxDrawDown() * 100,
            "ddd": self.analyzers["dd"].getLongestDrawDownDuration(),
            "win_rate": win_rate,
            "plr": plr,
            "trade_count": self.analyzers["trades"].getCount(),
        }

    @property
    def effects(self):
        return self.__effects

    def onFinish(self, bars):
        self.calculate_effects()

    @property
    def result(self):
        return self.__effects
