from myalgo.bar import Bars


class StrategyAnalyzer(object):
    """Base class for strategy analyzers.
    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self):
        self.__strat = None

    def beforeAttachImpl(self, strat):
        self.__strat = strat
        self.beforeAttach()

    @property
    def strat(self):
        return self.__strat

    @property
    def strategy(self):
        return self.__strat

    def beforeAttach(self):
        pass

    def attached(self):
        pass

    def beforeOnBars(self, bars: Bars):
        pass
