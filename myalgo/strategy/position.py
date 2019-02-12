

import datetime

from myalgo.order import State, Action
from myalgo.stratanalyzer.returns import PositionTracker


class PositionState(object):
    def onEnter(self, position):
        pass

    # Raise an exception if an order can't be submitted in the current state.
    def canSubmitOrder(self, position, order):
        raise NotImplementedError()

    def onOrderEvent(self, position, orderEvent):
        raise NotImplementedError()

    def isOpen(self, position):
        raise NotImplementedError()

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        raise NotImplementedError()


class WaitingEntryState(PositionState):
    def canSubmitOrder(self, position, order):
        if position.entryActive():
            raise Exception("The entry order is still active")

    def onOrderEvent(self, position, orderEvent):
        # Only entry order events are valid in this state.
        assert (position.getEntryOrder().id == orderEvent.order.id)

        if orderEvent.type in (State.FILLED, State.PARTIALLY_FILLED):
            position.switchState(OpenState())
            position.getStrategy().onEnterOk(position)
        elif orderEvent.type == State.CANCELED:
            assert (position.getEntryOrder().filled == 0)
            position.switchState(ClosedState())
            position.getStrategy().onEnterCanceled(position)

    def isOpen(self, position):
        return True

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        assert position.getAmounts() == 0
        assert position.getEntryOrder().is_active
        position.getStrategy().broker.cancelOrder(position.getEntryOrder())


class OpenState(PositionState):
    def onEnter(self, position):
        entryDateTime = position.getEntryOrder().finish_datetime
        position.setEntryDateTime(entryDateTime)

    def canSubmitOrder(self, position, order):
        # Only exit orders should be submitted in this state.
        pass

    def onOrderEvent(self, position, orderEvent):
        if position.getExitOrder() and position.getExitOrder().id == orderEvent.order.id:
            if orderEvent.type == State.FILLED:
                if position.getAmounts() == 0:
                    position.switchState(ClosedState())
                    position.getStrategy().onExitOk(position)
            elif orderEvent.type == State.CANCELED:
                assert (position.getAmounts() != 0)
                position.getStrategy().onExitCanceled(position)
        elif position.getEntryOrder().id == orderEvent.order.id:
            # Nothing to do since the entry order may be completely filled or canceled after a partial fill.
            assert (position.getAmounts() != 0)
        else:
            raise Exception("Invalid order event '%s' in OpenState" % (orderEvent.type))

    def isOpen(self, position):
        return True

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        assert (position.getAmounts() != 0)

        # Fail if a previous exit order is active.
        if position.exitActive():
            raise Exception("Exit order is active and it should be canceled first")

        # If the entry order is active, request cancellation.
        if position.entryActive():
            position.getStrategy().broker.cancel_order(position.getEntryOrder())

        position._submitExitOrder(stopPrice, limitPrice, goodTillCanceled)


class ClosedState(PositionState):
    def onEnter(self, position):
        # Set the exit datetime if the exit order was filled.
        if position.exitFilled():
            exitDateTime = position.getExitOrder().finish_datetime
            position.setExitDateTime(exitDateTime)

        assert (position.getAmounts() == 0)
        position.getStrategy().unregisterPosition(position)

    def canSubmitOrder(self, position, order):
        raise Exception("The position is closed")

    def onOrderEvent(self, position, orderEvent):
        raise Exception("Invalid order event '%s' in ClosedState" % (orderEvent.type))

    def isOpen(self, position):
        return False

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        pass


class Position(object):
    """Base class for positions.

    Positions are higher level abstractions for placing orders.
    They are escentially a pair of entry-exit orders and allow
    to track returns and PnL easier that placing orders manually.

    :param strategy: The strategy that this position belongs to.
    :type strategy: :class:`pyalgotrade.strategy.BaseStrategy`.
    :param entryOrder: The order used to enter the position.
    :type entryOrder: :class:`pyalgotrade.broker.Order`
    :param goodTillCanceled: True if the entry order should be set as good till canceled.
    :type goodTillCanceled: boolean.
    :param allOrNone: True if the orders should be completely filled or not at all.
    :type allOrNone: boolean.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, strategy, entryOrder, goodTillCanceled, allOrNone):
        # The order must be created but not submitted.
        assert entryOrder.is_initial

        self.__state = None
        self.__activeOrders = {}
        self.__shares = 0
        self.__strategy = strategy
        self.__entryOrder = None
        self.__entryDateTime = None
        self.__exitOrder = None
        self.__exitDateTime = None
        self.__posTracker = PositionTracker(entryOrder.round_quantity)
        self.__allOrNone = allOrNone

        self.switchState(WaitingEntryState())

        entryOrder.good_till_canceled = goodTillCanceled
        entryOrder.all_or_one = allOrNone
        self.__submitAndRegisterOrder(entryOrder)
        self.__entryOrder = entryOrder

    def __submitAndRegisterOrder(self, order):
        assert order.is_initial

        # Check if an order can be submitted in the current state.
        self.__state.canSubmitOrder(self, order)

        # This may raise an exception, so we wan't to submit the order before moving forward and registering
        # the order in the strategy.
        self.getStrategy().broker.submit_order(order)

        self.__activeOrders[order.id] = order
        self.getStrategy().registerPositionOrder(self, order)

    def setEntryDateTime(self, dateTime):
        self.__entryDateTime = dateTime

    def setExitDateTime(self, dateTime):
        self.__exitDateTime = dateTime

    def switchState(self, newState):
        self.__state = newState
        self.__state.onEnter(self)

    def getStrategy(self):
        return self.__strategy

    def getLastPrice(self):
        return self.__strategy.last_price(self.getInstrument())

    def getActiveOrders(self):
        return list(self.__activeOrders.values())

    def getAmounts(self):
        """Returns the number of shares.
        This will be a possitive number for a long position, and a negative number for a short position.

        .. note::
            If the entry order was not filled, or if the position is closed, then the number of shares will be 0.
        """
        return self.__shares

    def entryActive(self):
        """Returns True if the entry order is active."""
        return self.__entryOrder is not None and self.__entryOrder.is_active

    def entryFilled(self):
        """Returns True if the entry order was filled."""
        return self.__entryOrder is not None and self.__entryOrder.is_filled

    def exitActive(self):
        """Returns True if the exit order is active."""
        return self.__exitOrder is not None and self.__exitOrder.is_active

    def exitFilled(self):
        """Returns True if the exit order was filled."""
        return self.__exitOrder is not None and self.__exitOrder.is_filled

    def getEntryOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to enter the position."""
        return self.__entryOrder

    def getExitOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to exit the position. If this position hasn't been closed yet, None is returned."""
        return self.__exitOrder

    def getInstrument(self):
        """Returns the instrument used for this position."""
        return self.__entryOrder.instrument

    def getReturn(self, includeCommissions=True):
        """
        Calculates cumulative percentage returns up to this point.
        If the position is not closed, these will be unrealized returns.
        """

        # Deprecated in v0.18.

        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getReturn(price, includeCommissions)
        return ret

    def getPnL(self, includeCommissions=True):
        """
        Calculates PnL up to this point.
        If the position is not closed, these will be unrealized PnL.
        """
        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getPnL(price=price, includeCommissions=includeCommissions)
        return ret

    def cancelEntry(self):
        """Cancels the entry order if its active."""
        if self.entryActive():
            self.getStrategy().broker.cancelOrder(self.getEntryOrder())

    def cancelExit(self):
        """Cancels the exit order if its active."""
        if self.exitActive():
            self.getStrategy().broker.cancelOrder(self.getExitOrder())

    def exitMarket(self, goodTillCanceled=None):
        """Submits a market order to close this position.

        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, None, None, goodTillCanceled)

    def exitLimit(self, limitPrice, goodTillCanceled=None):
        """Submits a limit order to close this position.

        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, None, limitPrice, goodTillCanceled)

    def exitStop(self, stopPrice, goodTillCanceled=None):
        """Submits a stop order to close this position.

        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, stopPrice, None, goodTillCanceled)

    def exitStopLimit(self, stopPrice, limitPrice, goodTillCanceled=None):
        """Submits a stop limit order to close this position.

        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, stopPrice, limitPrice, goodTillCanceled)

    def _submitExitOrder(self, stopPrice, limitPrice, goodTillCanceled):
        assert (not self.exitActive())

        exitOrder = self.buildExitOrder(stopPrice, limitPrice)

        # If goodTillCanceled was not set, match the entry order.
        if goodTillCanceled is None:
            goodTillCanceled = self.__entryOrder.good_till_canceled
        exitOrder.good_till_canceled = goodTillCanceled
        exitOrder.all_or_one = self.__allOrNone

        self.__submitAndRegisterOrder(exitOrder)
        self.__exitOrder = exitOrder

    def onOrderEvent(self, orderEvent):
        self.__updatePosTracker(orderEvent)
        order = orderEvent.order
        if not order.is_active:
            del self.__activeOrders[order.id]

        # Update the number of shares.
        if orderEvent.type in (State.PARTIALLY_FILLED, State.FILLED):
            execInfo = orderEvent.info
            # roundQuantity is used to prevent bugs like the one triggered in testcases.bitstamp_test:TestCase.testRoundingBug
            if order.is_buy:
                self.__shares = order.round_quantity(self.__shares + execInfo.quantity)
            else:
                self.__shares = order.round_quantity(self.__shares - execInfo.quantity)

        self.__state.onOrderEvent(self, orderEvent)

    def __updatePosTracker(self, orderEvent):
        if orderEvent.type in (State.PARTIALLY_FILLED, State.FILLED):
            order = orderEvent.order
            execInfo = orderEvent.info
            if order.is_buy:
                self.__posTracker.buy(execInfo.quantity, execInfo.price, execInfo.commission)
            else:
                self.__posTracker.sell(execInfo.quantity, execInfo.price, execInfo.commission)

    def buildExitOrder(self, stopPrice, limitPrice):
        raise NotImplementedError()

    def isOpen(self):
        """Returns True if the position is open."""
        return self.__state.isOpen(self)

    def getAge(self):
        """Returns the duration in open state.

        :rtype: datetime.timedelta.

        .. note::
            * If the position is open, then the difference between the entry datetime and the datetime of the last bar is returned.
            * If the position is closed, then the difference between the entry datetime and the exit datetime is returned.
        """
        ret = datetime.timedelta()
        if self.__entryDateTime is not None:
            if self.__exitDateTime is not None:
                last = self.__exitDateTime
            else:
                last = self.__strategy.current_datetime
            ret = last - self.__entryDateTime
        return ret


# This class is reponsible for order management in long positions.
class LongPosition(Position):
    def __init__(self, strategy, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone):
        if limitPrice is None and stopPrice is None:
            entryOrder = strategy.broker.create_market_order(Action.BUY, instrument, quantity, False)
        elif limitPrice is not None and stopPrice is None:
            entryOrder = strategy.broker.create_limit_order(Action.BUY, instrument, limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            entryOrder = strategy.broker.create_stop_order(Action.BUY, instrument, stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            entryOrder = strategy.broker.create_stop_limit_order(Action.BUY, instrument, stopPrice, limitPrice,
                                                                 quantity)
        else:
            assert (False)

        super(LongPosition, self).__init__(strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getAmounts()
        assert (quantity > 0)
        if limitPrice is None and stopPrice is None:
            ret = self.getStrategy().broker.create_market_order(Action.SELL, self.getInstrument(), quantity, False)
        elif limitPrice is not None and stopPrice is None:
            ret = self.getStrategy().broker.create_limit_order(Action.SELL, self.getInstrument(), limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            ret = self.getStrategy().broker.create_stop_order(Action.SELL, self.getInstrument(), stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            ret = self.getStrategy().broker.create_stop_limit_order(Action.SELL, self.getInstrument(), stopPrice,
                                                                    limitPrice, quantity)
        else:
            assert (False)

        return ret


# This class is reponsible for order management in short positions.
class ShortPosition(Position):
    def __init__(self, strategy, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone):
        if limitPrice is None and stopPrice is None:
            entryOrder = strategy.broker.create_market_order(Action.SELL_SHORT, instrument, quantity, False)
        elif limitPrice is not None and stopPrice is None:
            entryOrder = strategy.broker.create_limit_order(Action.SELL_SHORT, instrument, limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            entryOrder = strategy.broker.create_stop_order(Action.SELL_SHORT, instrument, stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            entryOrder = strategy.broker.create_stop_limit_order(Action.SELL_SHORT, instrument, stopPrice, limitPrice,
                                                                 quantity)
        else:
            assert (False)

        super(ShortPosition, self).__init__(strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getAmounts() * -1
        assert (quantity > 0)
        if limitPrice is None and stopPrice is None:
            ret = self.getStrategy().broker.create_market_order(Action.BUY_TO_COVER, self.getInstrument(), quantity,
                                                                False)
        elif limitPrice is not None and stopPrice is None:
            ret = self.getStrategy().broker.create_limit_order(Action.BUY_TO_COVER, self.getInstrument(), limitPrice,
                                                               quantity)
        elif limitPrice is None and stopPrice is not None:
            ret = self.getStrategy().broker.create_stop_order(Action.BUY_TO_COVER, self.getInstrument(), stopPrice,
                                                              quantity)
        elif limitPrice is not None and stopPrice is not None:
            ret = self.getStrategy().broker.create_stop_limit_order(Action.BUY_TO_COVER, self.getInstrument(),
                                                                    stopPrice, limitPrice, quantity)
        else:
            assert (False)

        return ret
