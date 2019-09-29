from enum import Enum, unique

import numpy as np


@unique
class Frequency(Enum):
    # 现在最小的单位是1分钟了
    TRADE = -1
    MINUTE = 1
    HOUR = 60
    DAY = 24 * 60
    WEEK = 24 * 60 * 7
    MONTH = 24 * 60 * 31


"""
    实现了把数据存在numpy.array中，并且又能方便地访问
"""


class Bar:
    """

    """

    def __init__(self, start_date: np.datetime64, end_date: np.datetime64, data: np.array):
        """
            date is in `np.datetime64[m]`
        """
        assert data.shape == (9,)

        #
        # if ask_high < ask_low:
        #     raise Exception("high < low on %s" % start_date)
        # elif ask_high < ask_open:
        #     raise Exception("high < open on %s" % start_date)
        # elif ask_high < ask_close:
        #     raise Exception("high < close on %s" % start_date)
        # elif ask_low > ask_open:
        #     raise Exception("low > open on %s" % start_date)
        # elif ask_low > ask_close:
        #     raise Exception("low > close on %s" % start_date)
        #
        # if bid_high < bid_low:
        #     raise Exception("high < low on %s" % start_date)
        # elif bid_high < bid_open:
        #     raise Exception("high < open on %s" % start_date)
        # elif bid_high < bid_close:
        #     raise Exception("high < close on %s" % start_date)
        # elif bid_low > bid_open:
        #     raise Exception("low > open on %s" % start_date)
        # elif bid_low > bid_close:
        #     raise Exception("low > close on %s" % start_date)

        self.start_date = start_date
        self.end_date = end_date
        self.data = data

    @property
    def ask_open(self):
        return self.data[0]

    @property
    def ask_high(self):
        return self.data[2]

    @property
    def ask_low(self):
        return self.data[3]

    @property
    def ask_close(self):
        return self.data[1]

    @property
    def bid_open(self):
        return self.data[4]

    @property
    def bid_high(self):
        return self.data[6]

    @property
    def bid_low(self):
        return self.data[7]

    @property
    def bid_close(self):
        return self.data[5]

    @property
    def volume(self):
        return self.data[8]

    @property
    def out_price(self):
        return self.data[5]

    @property
    def in_price(self):
        return self.data[1]

    @property
    def price(self):
        return self.data[5]

    @property
    def dict(self):
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "ask_open": self.ask_open,
            "ask_low": self.ask_low,
            "ask_high": self.ask_high,
            "ask_close": self.ask_close,
            "bid_open": self.bid_open,
            "bid_low": self.bid_low,
            "bid_high": self.bid_high,
            "bid_close": self.bid_close,
            "volume": self.volume,
        }

    @staticmethod
    def from_dict(bar: dict):
        return Bar.from_bar(start_date=bar["start_date"], end_date=bar["end_date"],
                            ask_open=bar["ask_open"], ask_high=bar["ask_high"], ask_low=bar["ask_low"],
                            ask_close=bar["ask_close"],
                            bid_open=bar["bid_open"], bid_high=bar["bid_high"], bid_low=bar["bid_low"],
                            bid_close=bar["bid_close"],
                            volume=bar["volume"])

    @classmethod
    def from_bar(cls, start_date: np.datetime64, end_date: np.datetime64, ask_open: float, ask_close: float,
                 ask_high: float,
                 ask_low: float, bid_open: float, bid_close: float, bid_high: float,
                 bid_low: float, volume: float):
        data = np.array([ask_open, ask_close, ask_high, ask_low,
                         bid_open, bid_close, bid_high, bid_low, volume], dtype=np.float32)
        return cls(start_date, end_date, data)
