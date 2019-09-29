from abc import ABCMeta, abstractmethod

from myalgo.config import dispatchprio
from myalgo.event import Subject


class BaseBroker(Subject, metaclass=ABCMeta):
    def __init__(self, instruments):
        """
            TODO: 考虑下怎么把Feed什么的也抽象过来。。
        """
        self.instruments = instruments
        super(BaseBroker, self).__init__()

    def stop(self):
        pass

    def join(self):
        pass

    def dispatch(self):
        # All events were already emitted while handling barfeed events.
        pass

    @property
    def dispatch_priority(self):
        return dispatchprio.BROKER

    @abstractmethod
    def peek_datetime(self):
        pass

    @abstractmethod
    def cash(self, include_short):
        pass

    @abstractmethod
    def create_limit_order(self, action, instrument, limit_price, quantity):
        pass

    @abstractmethod
    def create_market_order(self, action, instrument, quantity, on_close):
        pass

    @abstractmethod
    def create_stop_order(self, action, instrument, price, quantity):
        pass

    @abstractmethod
    def create_stop_limit_order(self, action, instrument, stop_price, limit_price, quantity):
        pass

    @abstractmethod
    def commit_order_execution(self, fill_info, order_, datetime_):
        pass

    @abstractmethod
    def submit_order(self, order_):
        pass

    @abstractmethod
    def active_orders(self, instrument):
        pass

    @abstractmethod
    def cancel_order(self, order_):
        pass

    @property
    @abstractmethod
    def equity(self):
        pass
