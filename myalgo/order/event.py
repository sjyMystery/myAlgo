from myalgo.order.order import Order, State


class OrderEvent:
    def __init__(self, order: Order, _type: State, _info: str or None):
        self.__order = order
        self.__type = _type
        self.__info = _info

    @property
    def info(self):
        return self.__info

    @property
    def type(self):
        return self.__type

    @property
    def order(self):
        return self.__order
