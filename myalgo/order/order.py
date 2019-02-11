import abc
import functools
from datetime import datetime

from myalgo.bar import Bar
from myalgo.order import fill
from myalgo.order.action import Action
from myalgo.order.execution import Execution
from myalgo.order.state import State
from myalgo.order.type import Type


class Order:
    def __init__(self, type_: Type, action: Action, instrument, quantity: float, round_quantity=int):
        assert quantity is not None and quantity > 0
        assert type_ in Type

        self.__state = State.INITIAL
        self.__type = type_
        self.__action = action
        self.__quantity = quantity
        self.__roundQuantity = round_quantity
        self.__executionInfo = []
        self.__instrument = instrument
        self.__good_till_canceled = False
        self.__allOrNone = False
        self.__id = None
        self.__submitted_at = None
        self.__canceled_at = None
        self.__accepted_at = None

    def __repr__(self):
        return f'{self.instrument} {self.type} {self.action} {self.state} QUANT:{self.quantity}'

    @abc.abstractmethod
    def process(self, broker, bar1: Bar, bar2: Bar):
        return NotImplementedError('Not implemented!')

    @property
    def round_quantity(self):
        return self.__roundQuantity

    @property
    def good_till_canceled(self):
        return self.__good_till_canceled

    @good_till_canceled.setter
    def good_till_canceled(self, value):
        assert self.__state == State.INITIAL
        self.__good_till_canceled = value

    @property
    def all_or_one(self):
        return self.__allOrNone

    @all_or_one.setter
    def all_or_one(self, value):
        assert self.__state == State.INITIAL
        self.__allOrNone = value

    @property
    def type(self):
        return self.__type

    @property
    def is_buy(self):
        return self.action in [Action.BUY, Action.BUY_TO_COVER]

    @property
    def is_sell(self):
        return self.action in [Action.SELL, Action.SELL_SHORT]

    @property
    def is_active(self):
        return self.state not in [State.CANCELED, State.FILLED]

    @property
    def action(self):
        return self.__action

    @property
    def instrument(self):
        return self.__instrument

    @property
    def quantity(self):
        return self.__quantity

    def append_execution(self, execution: Execution):
        self.__executionInfo.append(execution)

    @property
    def executions(self):
        return self.__executionInfo

    @property
    def filled(self):
        def sum_quantity(x, y):
            return x + y.quantity

        return functools.reduce(sum_quantity, self.executions, 0)

    @property
    def filled_cost(self):
        def sum_total(x, y):
            return x + y.total

        return functools.reduce(sum_total, self.executions, 0)

    @property
    def total_commission(self):
        def sum_total(x, y: Execution):
            return x + y.commission

        return functools.reduce(sum_total, self.executions, 0)

    @property
    def avg_fill_price(self):
        assert self.filled , 'order not filled at all!'
        return self.filled_cost / float(self.filled)

    @property
    def remain(self):
        return self.__roundQuantity(self.quantity - self.filled)

    @property
    def id(self):
        return self.__id

    def submitted(self, _id, at: datetime):
        self.__id = _id
        self.__submitted_at = at
        return self

    def canceled(self, at: datetime):
        self.__canceled_at = at
        return self

    def accepted(self, at: datetime):
        self.__accepted_at = at
        return self

    @property
    def submitted_at(self):
        return self.__submitted_at

    @property
    def canceled_at(self):
        return self.__canceled_at

    @property
    def accepted_at(self):
        return self.__accepted_at

    @property
    def state(self):
        if self.canceled_at is not None:
            return State.CANCELED
        if self.submitted_at is None:
            return State.INITIAL

        if self.accepted_at is None:
            return State.SUBMITTED

        if self.filled is 0:
            return State.ACCEPTED
        elif self.remain is 0:
            return State.FILLED
        else:
            return State.PARTIALLY_FILLED

    @property
    def is_canceled(self):
        return self.canceled_at is not None

    @property
    def is_submitted(self):
        return self.state == State.SUBMITTED

    @property
    def is_accepted(self):
        return self.state == State.ACCEPTED

    @property
    def is_filled(self):
        return self.state == State.FILLED

    @property
    def is_partially_filled(self):
        return self.state == State.PARTIALLY_FILLED

    @property
    def is_initial(self):
        return self.state == State.INITIAL

    @property
    def finish_datetime(self):
        if self.executions is not None and len(self.executions) > 0:
            return self.executions[-1].datetime
        return None


class MarketOrder(Order):
    """
        Base Class for market orders
    """

    def __init__(self, action, instrument, quantity, on_close, round_quantity):
        super(MarketOrder, self).__init__(Type.MARKET, action, instrument, quantity, round_quantity)
        self.__onClose = on_close

    @property
    def fill_on_close(self):
        return self.__onClose

    def process(self, broker, bar1: Bar, bar2: Bar):
        if self.fill_on_close:
            price = bar2.ask_close if self.is_buy else bar2.bid_close
        else:
            price = bar2.ask_open if self.is_buy else bar2.bid_open
        assert price is not None
        return fill.FillInfo(price, self.quantity)


class LimitOrder(Order):
    def __init__(self, action: Action, instrument: str, limit_price: float, quantity: float, round_quantity=int):
        super(LimitOrder, self).__init__(Type.LIMIT, action, instrument, quantity, round_quantity)
        self.__limitPrice = limit_price

    @property
    def price(self):
        """Returns the limit price."""
        return self.__limitPrice

    def __repr__(self):
        return super(LimitOrder, self).__repr__()+f'\t PRICE:{self.price}'
    def process(self, broker, bar1: Bar, bar2: Bar):
        price = fill.get_limit_price_trigger(self.action, self.price, bar1, bar2)
        return None if price is None else fill.FillInfo(price, self.quantity)


class StopOrder(Order):
    """Base class for stop orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, price, quantity, round_quantity):
        super(StopOrder, self).__init__(Type.STOP, action, instrument, quantity, round_quantity)

        self.__stopPrice = price
        self.__stopHit = False

    @property
    def stop_hit(self):
        return self.__stopHit

    @property
    def price(self):
        """Returns the stop price."""
        return self.__stopPrice

    def process(self, broker, bar1: Bar, bar2: Bar):
        price_trigger = None
        if not self.__stopHit:
            price_trigger = fill.get_stop_price_trigger(self.action, self.price, bar1, bar2)
        if price_trigger is not None:
            self.__stopHit = True
        if self.stop_hit:
            """
                由于往往缺少数据，这里直接认为所有量全成交
            """
            fill_size = self.quantity
            if price_trigger is not None:
                price = price_trigger
            else:
                price = bar2.ask_open if self.is_buy else bar2.bid_open
            return fill.FillInfo(price, fill_size)
        return None


class StopLimitOrder(Order):
    """Base class for stop limit orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, stop_price, limit_price, quantity, round_quantity):
        super(StopLimitOrder, self).__init__(Type.STOP_LIMIT, action, instrument, quantity, round_quantity)

        self.__stopPrice = stop_price
        self.__limitPrice = limit_price
        self.__stopHit = False

    @property
    def stop_hit(self):
        return self.__stopHit

    @property
    def stop_price(self):
        """Returns the stop price."""
        return self.__stopPrice

    @property
    def limit_price(self):
        """Returns the limit price."""
        return self.__limitPrice

    def process(self, broker, bar1: Bar, bar2: Bar):
        price_trigger = None
        if not self.__stopHit:
            price_trigger = fill.get_stop_price_trigger(self.action, self.stop_price, bar1, bar2)

        self.__stopHit = price_trigger is not None

        if self.stop_hit:
            fill_size = self.quantity

            price = fill.get_limit_price_trigger(
                self.action,
                self.limit_price,
                bar1,
                bar2
            )
            if price is not None:
                # If we just hit the stop price, we need to make additional checks.
                if price_trigger is not None:
                    if self.is_buy:
                        # If the stop price triggered is lower than the limit price, then use that one.
                        # Else use the limit price.
                        price = min(price_trigger, self.limit_price)
                    else:
                        # If the stop price triggered is greater than the limit price, then use that one.
                        # Else use the limit price.
                        price = max(price_trigger, self.limit_price)
                return fill.FillInfo(price, fill_size)
        return None
