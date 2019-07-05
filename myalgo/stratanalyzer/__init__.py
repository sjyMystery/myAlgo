class StrategyAnalyzer(object):
    """Base class for strategy analyzers.
    .. note::
        This is a base class and should not be used directly.
    """

    def beforeAttach(self, strat):
        pass

    def attached(self, strat):
        pass

    def beforeOnBars(self, strat, bars):
        pass
