from myalgo.bar import Bar
from myalgo.order import Action


class FillInfo(object):
    def __init__(self, price: float, quantity: float):
        self.__price = price
        self.__quantity = quantity

    @property
    def price(self):
        return self.__price

    @property
    def quantity(self):
        return self.__quantity


# Returns the trigger price for a Limit or StopLimit order, or None if the limit price was not yet penetrated.
def get_limit_price_trigger(action: Action, price: float, bar1: Bar, bar2: Bar):
    """
        以最稳健的方式保证除入场
    :param action:
    :param price:
    :param bar1:
    :param bar2:
    :return:
    """
    ret = None
    if action in [Action.BUY, Action.BUY_TO_COVER]:
        if bar1.ask_close > price >= bar2.ask_low:
            return price

    elif action in [Action.SELL, Action.SELL_SHORT]:
        if bar1.bid_close < price <= bar2.bid_high:
            return price

    else:  # Unknown action
        assert False
    return ret


# Returns the trigger price for a Stop or StopLimit order, or None if the stop price was not yet penetrated.
def get_stop_price_trigger(action: Action, price: float, bar1: Bar, bar2: Bar):
    ret = None

    # If the bar is above the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    if action in [Action.BUY, Action.BUY_TO_COVER]:
        if bar1.ask_close < price:
            if bar2.ask_low > price:
                ret = bar2.ask_open
            elif price <= bar2.ask_high:
                return min(bar2.ask_open, price)
    # If the bar is below the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    elif action in [Action.SELL, Action.SELL_SHORT]:
        if bar1.bid_close > price:
            if bar2.bid_high < price:
                ret = bar2.bid_open
            elif price >= bar2.bid_low:
                return max(bar2.bid_open, price)
    else:  # Unknown action
        assert False

    return ret
