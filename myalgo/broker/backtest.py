from datetime import datetime

import six

import myalgo.logger as logger
from myalgo.bar import Bar, Bars
from myalgo.broker.commission import Commission
from myalgo.config import dispatchprio
from myalgo.event import Event
from myalgo.event import Subject
from myalgo.feed.barfeed import BarFeed
from myalgo.order import LimitOrder, Action, Order, Execution, OrderEvent, State, MarketOrder, StopLimitOrder, StopOrder
from myalgo.order.fill import FillInfo


class BackTestBroker(Subject):
    LOGGER_NAME = "back_test_log"

    def __init__(self, cash: float, bar_feed: BarFeed, commission: Commission, round_quantity=lambda x: int(x)):

        super(BackTestBroker, self).__init__()
        self.__commission = commission
        self.__bar_feed = bar_feed
        self.__cash = self.__initial_cash = cash

        self.__next_order_id = 0
        self.__active_orders = {}
        self.__quantities = {}
        self.__logger = logger.get_logger("Broker_log")

        self.__order_events = Event()

        self.__round = round_quantity

        self.__bar_feed.bar_events.subscribe(self.on_bars)
        self.__bar_feed.feed_reset_event.subscribe(self.__on_feed_change)
        self.__started = False

        self.instruments = bar_feed.instruments

    @property
    def instruments(self):
        return self.__instruments

    @property
    def quantities(self):
        return self.__quantities

    @instruments.setter
    def instruments(self, lists):
        assert not self.started, 'should not change instrument when started'
        self.__instruments = lists
        for instrument in lists:
            self.__quantities[instrument] = 0

    def __on_feed_change(self, bars):
        self.__reset()

    @property
    def started(self):
        return self.__started

    @property
    def dispatch_priority(self):
        return dispatchprio.BROKER

    @property
    def next_order_id(self):
        ret = self.__next_order_id
        self.__next_order_id += 1
        return ret

    @property
    def order_events(self):
        return self.__order_events

    def register_order(self, order_: Order):
        assert (order_.id not in self.__active_orders)
        assert (order_.id is not None)
        self.__active_orders[order_.id] = order_

    def unregister_order(self, order_: Order):
        assert (order_.id in self.__active_orders)
        assert (order_.id is not None)
        del self.__active_orders[order_.id]

    @property
    def logger(self):
        return self.__logger

    def get_bar(self, bars, instrument):
        ret = bars.bar(instrument)
        if ret is None:
            ret = self.__bar_feed.last_bar(instrument)
        return ret

    def cash(self, include_short=True):
        ret = self.__cash
        if not include_short and self.__bar_feed.current_bars is not None:
            bars = self.__bar_feed.current_bars
            for instrument, shares in six.iteritems(self.__quantities):
                if shares < 0:
                    instrument_price = self.get_bar(bars, instrument).in_price
                    ret += instrument_price * shares
        return ret

    @property
    def equity(self):
        """Returns the portfolio value (cash + shares * price)."""
        ret = self.cash()
        for instrument, shares in six.iteritems(self.__quantities):
            instrument_price = self.__bar_feed.last_bar(instrument).out_price
            assert instrument_price is not None, "Price for %s is missing" % instrument
            ret += instrument_price * shares
        return ret

    def create_limit_order(self, action: Action, instrument: str, limit_price: float, quantity: float):
        return LimitOrder(action, instrument, limit_price=limit_price, quantity=quantity,
                          round_quantity=self.__round)

    def create_market_order(self, action: Action, instrument: str, quantity: float, on_close=False):
        # In order to properly support market-on-close with intraday feeds I'd need to know about different
        # exchange/market trading hours and support specifying routing an order to a specific exchange/market.
        # Even if I had all this in place it would be a problem while paper-trading with a live feed since
        # I can't tell if the next bar will be the last bar of the market session or not.
        return MarketOrder(action, instrument, quantity, on_close, round_quantity=self.__round)

    def create_stop_order(self, action: Action, instrument: str, price: float, quantity: float):
        return StopOrder(action, instrument, price, quantity, round_quantity=self.__round)

    def create_stop_limit_order(self, action: Action, instrument: str, stop_price: float, limit_price: float,
                                quantity: float):
        return StopLimitOrder(action, instrument, stop_price, limit_price, quantity, round_quantity=self.__round)

    # Tries to commit an order execution.
    def commit_order_execution(self, fill_info: FillInfo, order_: Order, datetime_: datetime):
        price = fill_info.price
        quantity = fill_info.quantity

        if order_.is_buy:
            cost = price * quantity * -1
            assert (cost < 0)
            shares_delta = quantity
        elif order_.is_sell:
            cost = price * quantity
            assert (cost > 0)
            shares_delta = quantity * -1
        else:  # Unknown action
            assert False

        commission = self.__commission.calculate(order_, price, quantity)
        cost -= commission
        resulting_cash = self.__cash + cost

        # Check that we're ok on cash after the commission.
        if resulting_cash >= 0:

            # Update the order before updating internal state since addExecutionInfo may raise.
            # addExecutionInfo should switch the order state.
            execution = Execution(price, quantity, commission, datetime_)
            order_.append_execution(execution)

            # Commit the order execution.
            self.__cash = resulting_cash

            updated_shares = order_.round_quantity(
                self.__quantities[order_.instrument] + shares_delta
            )
            self.__quantities[order_.instrument] = updated_shares

            # Notify the order update
            if order_.is_filled:
                self.unregister_order(order_)
                self.notify_order_event(OrderEvent(order_, State.FILLED, execution))
            elif order_.is_partially_filled:
                self.notify_order_event(OrderEvent(order_, State.PARTIALLY_FILLED, execution))
            else:
                assert False
        else:
            self.__logger.debug("Not enough cash to fill %s order [%s] for %s share/s" % (
                order_.instrument,
                order_.id,
                order_.remain
            ))

    def submit_order(self, order_: Order):
        if order_.is_initial:
            order_.submitted(self.next_order_id, self.current_datetime)
            self.register_order(order_)
            self.notify_order_event(OrderEvent(order_, State.SUBMITTED, None))
        else:
            raise Exception("The order was already processed")

    # Return True if further processing is needed.
    def __preprocess_order(self, order_: Order, bar_: Bar):
        ret = True

        # For non-GTC orders we need to check if the order has expired.
        if not order_.good_till_canceled:

            current = bar_.start_date

            expired = current.date() > order_.accepted_at.date()

            # Cancel the order if it is expired.
            if expired:
                ret = False
                self.unregister_order(order_)
                order_.canceled(current)
                self.notify_order_event(OrderEvent(order_, State.CANCELED, "Expired"))

        return ret

    def __postprocess_order(self, order_: Order, bar_: Bar):
        # For non-GTC orders and daily (or greater) bars we need to check if orders should expire right now
        # before waiting for the next bar.
        if not order_.good_till_canceled:
            expired = False

            # Cancel the order if it will expire in the next bar.
            if expired:
                self.unregister_order(order_)
                order_.canceled(bar_.start_date)
                self.notify_order_event(OrderEvent(order_, State.CANCELLED, "Expired"))

    def __process_order(self, order_, bar1: Bar, bar2: Bar):
        if not self.__preprocess_order(order_, bar2):
            return
        # Double dispatch to the fill strategy using the concrete order type.
        fill_info = order_.process(self, bar1, bar2)
        if fill_info is not None:
            self.commit_order_execution(fill_info, order_, bar2.start_date)

        if order_.is_active:
            self.__postprocess_order(order_, bar2)

    def __on_bars_impl(self, order_, bars1: Bars, bars2: Bars):
        # IF WE'RE DEALING WITH MULTIPLE INSTRUMENTS WE SKIP ORDER PROCESSING IF THERE IS NO BAR FOR THE ORDER'S
        # INSTRUMENT TO GET THE SAME BEHAVIOUR AS IF WERE BE PROCESSING ONLY ONE INSTRUMENT.
        bar1 = bars1.bar(order_.instrument)
        bar2 = bars2.bar(order_.instrument)
        if bar1 is not None and bar2 is not None:
            # Switch from SUBMITTED -> ACCEPTED
            if order_.is_submitted:
                order_.accepted(bar2.start_date)
                self.notify_order_event(
                    OrderEvent(order_, State.ACCEPTED, None))

            if order_.is_active:
                # This may trigger orders to be added/removed from __activeOrders.
                self.__process_order(order_, bar1, bar2)
            else:
                # If an order is not active it should be because it was c11anceled in this same loop and it should
                # have been removed.
                assert order_.is_canceled
                assert order_ not in self.__active_orders

    def on_bars(self, datetime_, bars1: Bars, bars2: Bars):

        # This is to froze the orders that will be processed in this event, to avoid new getting orders introduced
        # and processed on this very same event.
        orders_to_process = list(self.__active_orders.values())

        for order_ in orders_to_process:
            # This may trigger orders to be added/removed from __activeOrders.
            self.__on_bars_impl(order_, bars1, bars2)

    @property
    def active_instruments(self):
        return [instrument for instrument, shares in six.iteritems(self.__quantities) if shares != 0]

    def active_orders(self, instrument=None):
        if instrument is None:
            ret = list(self.__active_orders.values())
        else:
            ret = [order_ for order_ in self.__active_orders.values() if order_.instrument == instrument]
        return ret

    def cancel_order(self, order_: Order):
        active_order = self.__active_orders.get(order_.id)
        if active_order is None:
            raise Exception("The order is not active anymore")
        if active_order.is_filled:
            raise Exception("Can't cancel order that has already been filled")

        self.unregister_order(active_order)
        active_order.canceled(self.current_datetime)
        self.notify_order_event(
            OrderEvent(active_order, State.CANCELED, "User requested cancellation")
        )

    @property
    def commission(self):
        """Returns the strategy used to calculate order commissions.

        :rtype: :class:`Commission`.
        """
        return self.__commission

    @commission.setter
    def commission(self, commission):
        """Sets the strategy to use to calculate order commissions.

        :param commission: An object responsible for calculating order commissions.
        :type commission: :class:`Commission`.
        """

        self.__commission = commission

    @property
    def current_datetime(self):
        return self.__bar_feed.current_datetime

    @property
    def bar_feed(self):
        return self.__bar_feed

    def start(self):
        super(BackTestBroker, self).start()
        self.__started = True

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        # If there are no more events in the barfeed, then there is nothing left for us to do since all processing took
        # place while processing barfeed events.
        return self.bar_feed.eof()

    def dispatch(self):
        # All events were already emitted while handling barfeed events.
        pass

    def peek_datetime(self):
        return None

    def notify_order_event(self, event: OrderEvent):
        return self.__order_events.emit(self, event)

    def __reset(self):
        self.__started = False
        self.__cash = self.__initial_cash
        self.__next_order_id = 0
        self.__active_orders = {}
        self.instruments = self.bar_feed.instruments
