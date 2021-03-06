import abc

from myalgo import logger
from myalgo.broker import BaseBroker
from myalgo.dataseries import BarDataSeries
from myalgo.event import Dispatcher
from myalgo.event import Event
from myalgo.order import Action, LimitOrder, Order
from myalgo.strategy import position


class BaseStrategy:
    LOGGER_NAME = "BaseStrategyLog"

    def __init__(self, broker: BaseBroker, series_max_len=None):
        self.__broker = broker
        self.__activePositions = set()
        self.__orderToPosition = {}
        self.__barsProcessedEvent = Event()
        self.__analyzers = []
        self.__namedAnalyzers = {}
        self.__resampledBarFeeds = []
        self.__dispatcher = Dispatcher()
        self.__broker.order_events.subscribe(self.__onOrderEvent)
        self.bar_feed.bar_events.subscribe(self.__onBars)
        self.bar_feed.feed_reset_event.subscribe(self.reset)

        # onStart will be called once all subjects are started.
        self.__dispatcher.getStartEvent().subscribe(self.onStart)
        self.__dispatcher.getIdleEvent().subscribe(self.__onIdle)

        # It is important to dispatch broker events before feed events, specially if we're backtesting.
        self.__dispatcher.addSubject(self.broker)
        self.__dispatcher.addSubject(self.bar_feed)

        # Initialize logging.
        self.__logger = logger.get_logger(BaseStrategy.LOGGER_NAME)

        self.use_event_datetime_logs = True

        self.__onEnterOkEvent = Event()
        self.__onEnterCanceledEvent = Event()
        self.__onExitOkEvent = Event()
        self.__onExitCanceledEvent = Event()

        self.__onEnterOkEvent.subscribe(self.onEnterOk)
        self.__onEnterCanceledEvent.subscribe(self.onEnterCanceled)
        self.__onExitOkEvent.subscribe(self.onExitOk)
        self.__onExitCanceledEvent.subscribe(self.onExitCanceled)
        self.__onEnterStartEvent = Event()
        self.__onExitStartEvent = Event()

        """
            我们尝试把数据序列记在策略中
            TODO: 对于离线的回测，这个过程可以利用本来的数据
        """

        instruments = broker.instruments

        self.bar_series = dict()
        self.max_series_length = series_max_len

        for instrument in instruments:
            self.bar_series[instrument] = BarDataSeries(max_len=series_max_len)

        """
            反正都要用，为何不把所有Positions管理起来呢
        """
        self.__positions = []
        self.__onEnterStartEvent.subscribe(self.__on_enter_start)

    def __on_enter_start(self, position):
        self.__positions.append(position)

    @property
    def positions(self):
        return self.__positions

    @property
    def enter_start_event(self):
        return self.__onEnterStartEvent

    @property
    def exit_start_event(self):
        return self.__onExitStartEvent

    @property
    def enter_ok_event(self):
        return self.__onEnterOkEvent

    @property
    def exit_ok_event(self):
        return self.__onExitOkEvent

    @property
    def enter_canceled_event(self):
        return self.__onEnterCanceledEvent

    @property
    def exit_canceled_event(self):
        return self.__onExitCanceledEvent

    def notify_enter_start(self, position):
        self.__onEnterStartEvent.emit(position)

    def notify_exit_start(self, position):
        self.__onExitStartEvent.emit(position)

    def notify_enter_ok(self, position):
        self.__onEnterOkEvent.emit(position)

    def notify_enter_canceled(self, position):
        self.__onEnterCanceledEvent.emit(position)

    def notify_exit_canceled(self, position):
        self.__onExitCanceledEvent.emit(position)

    def notify_exit_ok(self, position):
        self.__onExitOkEvent.emit(position)

    def reset(self, bars):
        self.__activePositions = set()
        self.__orderToPosition = {}
        self.__barsProcessedEvent = Event()
        self.__analyzers = []
        self.__namedAnalyzers = {}
        self.__resampledBarFeeds = []
        self.__dispatcher = Dispatcher()
        for series in self.bar_series.values():
            series.reset(self.max_series_length)

    @property
    def use_event_datetime_logs(self):
        return logger.Formatter.DATETIME_HOOK is self.dispatcher.getCurrentDateTime

    @use_event_datetime_logs.setter
    def use_event_datetime_logs(self, use: bool):
        if use:
            logger.Formatter.DATETIME_HOOK = self.dispatcher.getCurrentDateTime
        else:
            logger.Formatter.DATETIME_HOOK = None

    @property
    def broker(self):
        return self.__broker

    @property
    def bars_processed_events(self):
        return self.__barsProcessedEvent

    @property
    def bar_feed(self):
        return self.broker.bar_feed

    @property
    def feed(self):
        return self.bar_feed

    @property
    def current_datetime(self):
        return self.bar_feed.current_datetime

    @property
    def dispatcher(self):
        return self.__dispatcher

    def last_price(self, instrument: str):
        ret = None
        bar = self.bar_feed.last_bar(instrument)
        if bar is not None:
            ret = bar.price
        return ret

    def limitOrder(self, instrument: str, limit_price: float, quantity: float, goodTill_canceled: bool = False,
                   all_or_none: bool = False):
        ret = None
        if quantity > 0:
            ret: LimitOrder = self.broker.create_limit_order(Action.BUY, instrument, limit_price,
                                                             quantity)
        elif quantity < 0:
            ret: LimitOrder = self.broker.create_limit_order(Action.SELL, instrument, limit_price,
                                                             quantity * -1)
        if ret:
            ret.good_till_canceled = goodTill_canceled
            ret.all_or_one = all_or_none
            self.broker.submit_order(ret)
        return ret

    def stopLimitOrder(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Submits a stop limit order.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: The amount of shares. Positive means buy, negative means sell.
        :type quantity: int/float.
        :param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the order should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.broker.StopLimitOrder` submitted.
        """

        ret = None
        if quantity > 0:
            ret = self.broker.create_stop_limit_order(
                Action.BUY, instrument, stopPrice, limitPrice, quantity)
        elif quantity < 0:
            ret = self.broker.create_stop_limit_order(
                Action.SELL, instrument, stopPrice, limitPrice, quantity * -1)
        if ret:
            ret.good_till_canceled = goodTillCanceled
            ret.all_or_one = allOrNone
            self.broker.submit_order(ret)
        return ret

    def enterLong(self, instrument, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.MarketOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.LongPosition(self, instrument, None, None, quantity, goodTillCanceled,
                                     allOrNone)

    def enterShort(self, instrument, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.MarketOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.ShortPosition(self, instrument, None, None, quantity, goodTillCanceled,
                                      allOrNone)

    def enterLongLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.LimitOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.LongPosition(self, instrument, None, limitPrice, quantity,
                                     goodTillCanceled, allOrNone)

    def enterShortLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.LimitOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.ShortPosition(self, instrument, None, limitPrice, quantity,
                                      goodTillCanceled, allOrNone)

    def enterLongStop(self, instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.StopOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.LongPosition(self, instrument, stopPrice, None, quantity, goodTillCanceled,
                                     allOrNone)

    def enterShortStop(self, instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.StopOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.ShortPosition(self, instrument, stopPrice, None, quantity,
                                      goodTillCanceled, allOrNone)

    def enterLongStopLimit(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.StopLimitOrder` order to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.LongPosition(self, instrument, stopPrice, limitPrice, quantity,
                                     goodTillCanceled, allOrNone)

    def enterShortStopLimit(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.StopLimitOrder` order to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: The Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return position.ShortPosition(self, instrument, stopPrice, limitPrice, quantity,
                                      goodTillCanceled, allOrNone)

    @property
    def result(self):
        return self.broker.equity

    @property
    def active_positions(self):
        return self.__activePositions

    @property
    def order_to_positions(self):
        return self.order_to_positions

    @property
    def logger(self):
        return self.__logger

    def debug(self, msg):
        """Logs a message with level DEBUG on the strategy logger."""
        self.logger.debug(msg)

    def info(self, msg):
        """Logs a message with level INFO on the strategy logger."""
        self.logger.info(msg)

    def warning(self, msg):
        """Logs a message with level WARNING on the strategy logger."""
        self.logger.warning(msg)

    def error(self, msg):
        """Logs a message with level ERROR on the strategy logger."""
        self.logger.error(msg)

    def critical(self, msg):
        """Logs a message with level CRITICAL on the strategy logger."""
        self.logger.critical(msg)

    def registerPositionOrder(self, position, order: Order):
        self.__activePositions.add(position)
        assert order.is_active  # Why register an inactive order ?
        self.__orderToPosition[order.id] = position

    def unregisterPositionOrder(self, position, order: Order):
        del self.__orderToPosition[order.id]

    def unregisterPosition(self, position):
        assert (not position.isOpen())
        self.__activePositions.remove(position)

    def __notifyAnalyzers(self, lambdaExpression):
        for s in self.__analyzers:
            lambdaExpression(s)

    def attachAnalyzerEx(self, strategyAnalyzer, name=None):
        if strategyAnalyzer not in self.__analyzers:
            if name is not None:
                if name in self.__namedAnalyzers:
                    raise Exception(
                        "A different analyzer named '%s' was already attached" % name)
                self.__namedAnalyzers[name] = strategyAnalyzer

            strategyAnalyzer.beforeAttachImpl(self)
            self.__analyzers.append(strategyAnalyzer)
            strategyAnalyzer.attached()

    """
        下面开始是事件
    """

    def onEnterOk(self, position):
        """Override (optional) to get notified when the order submitted to enter a position was filled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`pyalgotrade.strategy.position.Position`.
        """
        pass

    def onEnterCanceled(self, position):
        """Override (optional) to get notified when the order submitted to enter a position was canceled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`pyalgotrade.strategy.position.Position`.
        """
        pass

    # Called when the exit order for a position was filled.
    def onExitOk(self, position):
        """Override (optional) to get notified when the order submitted to exit a position was filled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`pyalgotrade.strategy.position.Position`.
        """
        pass

    # Called when the exit order for a position was canceled.
    def onExitCanceled(self, position):
        """Override (optional) to get notified when the order submitted to exit a position was canceled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`pyalgotrade.strategy.position.Position`.
        """
        pass

    """Base class for strategies. """

    def onStart(self):
        """Override (optional) to get notified when the strategy starts executing. The default implementation is empty. """
        pass

    def onFinish(self, bars):
        """Override (optional) to get notified when the strategy finished executing. The default implementation is empty.

        :param bars: The last bars processed.
        :type bars: :class:`pyalgotrade.bar.Bars`.
        """
        pass

    def onIdle(self):
        """Override (optional) to get notified when there are no events.

       .. note::
            In a pure backtesting scenario this will not be called.
        """
        pass

    @abc.abstractmethod
    def onBars(self, datetime, bars):
        """Override (**mandatory**) to get notified when new bars are available. The default implementation raises an Exception.

        **This is the method to override to enter your trading logic and enter/exit positions**.

        :param bars: The current bars.
        :type bars: :class:`pyalgotrade.bar.Bars`.
        """
        raise NotImplementedError()

    def onOrderUpdated(self, order):
        """Override (optional) to get notified when an order gets updated.

        :param order: The order updated.
        :type order: :class:`pyalgotrade.broker.Order`.
        """
        pass

    def __onIdle(self):
        # Force a resample check to avoid depending solely on the underlying
        # barfeed events.
        for resampledBarFeed in self.__resampledBarFeeds:
            resampledBarFeed.checkNow(self.current_datetime)

        self.onIdle()

    def __onOrderEvent(self, broker_, orderEvent):
        order = orderEvent.order
        self.onOrderUpdated(order)
        # Notify the position about the order event.
        pos = self.__orderToPosition.get(order.id, None)
        if pos is not None:
            # Unlink the order from the position if its not active anymore.
            if not order.is_active:
                self.unregisterPositionOrder(pos, order)

            pos.onOrderEvent(orderEvent)

    def __appendToSeries(self, bars):
        for instrument, bar in bars.items():
            self.bar_series[instrument].append(bar)

    def __onBars(self, dateTime, bars1, bars2):
        # THE ORDER HERE IS VERY IMPORTANT

        # 0: Append The bar Into the dataseries
        self.__appendToSeries(bars2)
        # 1: Let analyzers process bars.
        self.__notifyAnalyzers(lambda s: s.beforeOnBars(bars2))
        # 2: Let the strategy process current bars and submit orders.
        self.onBars(dateTime, bars2)

        # 3: Notify that the bars were processed.
        self.__barsProcessedEvent.emit(self, bars2)

    def run(self):
        """Call once (**and only once**) to run the strategy."""
        self.__dispatcher.run()
        if self.bar_feed.last_bars is not None:
            self.onFinish(self.bar_feed.last_bars)
        else:
            self.logger.warn('BAR IS EMPTY!')

    def stop(self):
        """Stops a running strategy."""
        self.__dispatcher.stop()

    def attachAnalyzer(self, strategyAnalyzer):
        self.attachAnalyzerEx(strategyAnalyzer)

    def getNamedAnalyzer(self, name):
        return self.__namedAnalyzers.get(name, None)
