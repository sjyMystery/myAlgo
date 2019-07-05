from .basic import BaseStrategy
from ..broker import BackTestBroker
from ..stratanalyzer.drawdown import DrawDown
from ..stratanalyzer.returns import Returns
from ..stratanalyzer.sharpe import SharpeRatio
from ..stratanalyzer.trades import Trades


class BackTestStrategy(BaseStrategy):
    def onBars(self, datetime, bars):
        return NotImplementedError()

    def __init__(self, broker: BackTestBroker):
        super(BackTestStrategy, self).__init__(broker)

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

        profits = self.analyzers["trades"].getProfits()
        losses = self.analyzers["trades"].getLosses()
        if losses.mean() != 0:
            plr = profits.mean() / abs(losses.mean())
        else:
            plr = None

        win_rate = self.analyzers["trades"].getProfitableCount() / self.analyzers["trades"].getCount() * 100 \
            if self.analyzers["trades"].getCount() != 0 else None

        self.__effects = {
            "ret": self.analyzers["ret"].getCumulativeReturns()[-1] * 100,
            "sharp": self.analyzers["sharpe"].getSharpeRatio(0.05),
            "dd": self.analyzers["dd"].getMaxDrawDown() * 100,
            "ddd": self.analyzers["dd"].getLongestDrawDownDuration(),
            "win_rate": win_rate,
            "plr": plr,
        }

    @property
    def effects(self):
        return self.__effects

    def onFinish(self, bars):
        self.calculate_effects()
