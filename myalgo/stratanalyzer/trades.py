

import numpy as np

from myalgo import stratanalyzer
from myalgo.order import State, Action
from myalgo.stratanalyzer import returns


class Trades(stratanalyzer.StrategyAnalyzer):
    """A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that records the profit/loss
    and returns of every completed trade.

    .. note::
        This analyzer operates on individual completed trades.
        For example, lets say you start with a $1000 cash, and then you buy 1 share of XYZ
        for $10 and later sell it for $20:

            * The trade's profit was $10.
            * The trade's return is 100%, even though your whole portfolio went from $1000 to $1020, a 2% return.
    """

    def __init__(self):
        super(Trades, self).__init__()
        self.__all = []
        self.__profits = []
        self.__losses = []
        self.__allReturns = []
        self.__positiveReturns = []
        self.__negativeReturns = []
        self.__allCommissions = []
        self.__profitableCommissions = []
        self.__unprofitableCommissions = []
        self.__evenCommissions = []
        self.__evenTrades = 0
        self.__posTrackers = {}

    def __updateTrades(self, posTracker):
        price = 0  # The price doesn't matter since the position should be closed.
        assert posTracker.getPosition() == 0
        netProfit = posTracker.getPnL(price)
        netReturn = posTracker.getReturn(price)

        if netProfit > 0:
            self.__profits.append(netProfit)
            self.__positiveReturns.append(netReturn)
            self.__profitableCommissions.append(posTracker.getCommissions())
        elif netProfit < 0:
            self.__losses.append(netProfit)
            self.__negativeReturns.append(netReturn)
            self.__unprofitableCommissions.append(posTracker.getCommissions())
        else:
            self.__evenTrades += 1
            self.__evenCommissions.append(posTracker.getCommissions())

        self.__all.append(netProfit)
        self.__allReturns.append(netReturn)
        self.__allCommissions.append(posTracker.getCommissions())

        posTracker.reset()

    def __updatePosTracker(self, posTracker, price, commission, quantity):
        currentShares = posTracker.getPosition()

        if currentShares > 0:  # Current position is long
            if quantity > 0:  # Increase long position
                posTracker.buy(quantity, price, commission)
            else:
                newShares = currentShares + quantity
                if newShares == 0:  # Exit long.
                    posTracker.sell(currentShares, price, commission)
                    self.__updateTrades(posTracker)
                elif newShares > 0:  # Sell some shares.
                    posTracker.sell(quantity * -1, price, commission)
                else:  # Exit long and enter short. Use proportional commissions.
                    proportionalCommission = commission * currentShares / float(quantity * -1)
                    posTracker.sell(currentShares, price, proportionalCommission)
                    self.__updateTrades(posTracker)
                    proportionalCommission = commission * newShares / float(quantity)
                    posTracker.sell(newShares * -1, price, proportionalCommission)
        elif currentShares < 0:  # Current position is short
            if quantity < 0:  # Increase short position
                posTracker.sell(quantity * -1, price, commission)
            else:
                newShares = currentShares + quantity
                if newShares == 0:  # Exit short.
                    posTracker.buy(currentShares * -1, price, commission)
                    self.__updateTrades(posTracker)
                elif newShares < 0:  # Re-buy some shares.
                    posTracker.buy(quantity, price, commission)
                else:  # Exit short and enter long. Use proportional commissions.
                    proportionalCommission = commission * currentShares * -1 / float(quantity)
                    posTracker.buy(currentShares * -1, price, proportionalCommission)
                    self.__updateTrades(posTracker)
                    proportionalCommission = commission * newShares / float(quantity)
                    posTracker.buy(newShares, price, proportionalCommission)
        elif quantity > 0:
            posTracker.buy(quantity, price, commission)
        else:
            posTracker.sell(quantity * -1, price, commission)

    def __onOrderEvent(self, broker_, orderEvent):
        # Only interested in filled or partially filled orders.
        if orderEvent.type not in (State.PARTIALLY_FILLED, State.FILLED):
            return

        order = orderEvent.order

        # Get or create the tracker for this instrument.
        try:
            posTracker = self.__posTrackers[order.instrument]
        except KeyError:
            posTracker = returns.PositionTracker(order.round_quantity)
            self.__posTrackers[order.instrument] = posTracker

        # Update the tracker for this order.
        execInfo = orderEvent.info
        price = execInfo.price
        commission = execInfo.commission
        action = order.action
        if action in [Action.BUY, Action.BUY_TO_COVER]:
            quantity = execInfo.quantity
        elif action in [Action.SELL, Action.SELL_SHORT]:
            quantity = execInfo.quantity * -1
        else:  # Unknown action
            assert (False)

        self.__updatePosTracker(posTracker, price, commission, quantity)

    def attached(self):
        self.strat.broker.order_events.subscribe(self.__onOrderEvent)

    def getCount(self):
        """Returns the total number of trades."""
        return len(self.__all)

    def getProfitableCount(self):
        """Returns the number of profitable trades."""
        return len(self.__profits)

    def getUnprofitableCount(self):
        """Returns the number of unprofitable trades."""
        return len(self.__losses)

    def getEvenCount(self):
        """Returns the number of trades whose net profit was 0."""
        return self.__evenTrades

    def getAll(self):
        """Returns a numpy.array with the profits/losses for each trade."""
        return np.asarray(self.__all)

    def getProfits(self):
        """Returns a numpy.array with the profits for each profitable trade."""
        return np.asarray(self.__profits)

    def getLosses(self):
        """Returns a numpy.array with the losses for each unprofitable trade."""
        return np.asarray(self.__losses)

    def getAllReturns(self):
        """Returns a numpy.array with the returns for each trade."""
        return np.asarray(self.__allReturns)

    def getPositiveReturns(self):
        """Returns a numpy.array with the positive returns for each trade."""
        return np.asarray(self.__positiveReturns)

    def getNegativeReturns(self):
        """Returns a numpy.array with the negative returns for each trade."""
        return np.asarray(self.__negativeReturns)

    def getCommissionsForAllTrades(self):
        """Returns a numpy.array with the commissions for each trade."""
        return np.asarray(self.__allCommissions)

    def getCommissionsForProfitableTrades(self):
        """Returns a numpy.array with the commissions for each profitable trade."""
        return np.asarray(self.__profitableCommissions)

    def getCommissionsForUnprofitableTrades(self):
        """Returns a numpy.array with the commissions for each unprofitable trade."""
        return np.asarray(self.__unprofitableCommissions)

    def getCommissionsForEvenTrades(self):
        """Returns a numpy.array with the commissions for each trade whose net profit was 0."""
        return np.asarray(self.__evenCommissions)
