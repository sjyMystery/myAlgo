import abc

import six

from myalgo.order.order import Order


######################################################################
# Commission models


@six.add_metaclass(abc.ABCMeta)
class Commission(object):
    """Base class for implementing different commission schemes.

    .. note::
        This is a base class and should not be used directly.
    """

    @abc.abstractmethod
    def calculate(self, order: Order, price: float, quantity: float):
        """Calculates the commission for an order execution.

        :param order: The order being executed.
        :type order: :class:`order.Order`.
        :param price: The price for each share.
        :type price: float.
        :param quantity: The order size.
        :type quantity: float.
        :rtype: float.
        """
        raise NotImplementedError()


class NoCommission(Commission):
    """A :class:`Commission` class that always returns 0."""

    def calculate(self, order: Order, price: float, quantity: float):
        return 0


class FixedPerTrade(Commission):
    """A :class:`Commission` class that charges a fixed amount for the whole trade.

    :param amount: The commission for an order.
    :type amount: float.
    """

    def __init__(self, amount):
        super(FixedPerTrade, self).__init__()
        self.__amount = amount

    def calculate(self, order: Order, price: float, quantity: float):
        ret = 0
        # Only charge the first fill.
        if order.executions is None:
            ret = self.__amount
        return ret


class TradePercentage(Commission):
    """A :class:`Commission` class that charges a percentage of the whole trade.

    :param percentage: The percentage to charge. 0.01 means 1%, and so on. It must be smaller than 1.
    :type percentage: float.
    """

    def __init__(self, percentage):
        super(TradePercentage, self).__init__()
        assert (percentage < 1)
        self.__percentage = percentage

    def calculate(self, order: Order, price: float, quantity: float):
        return price * quantity * self.__percentage
