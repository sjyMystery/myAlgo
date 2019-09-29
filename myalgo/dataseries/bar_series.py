import numpy as np

from myalgo.event import Event
from ..bar import Bar, Frequency

DEFAULT_MAX_LEN = 30000000


def check_max_len(max_len):
    if max_len is None or max_len <= 0:
        return DEFAULT_MAX_LEN
    else:
        return max_len


class PriceSeriesImpl:
    def __init__(self, prices, timestamps, current, max_len):
        self.reset(prices, timestamps, current, max_len)

    def __getitem__(self, key):
        """
            我们将数据截取成对应的形状后再进行访问
        """
        return self.prices[:self.current][key]

    def reset(self, prices=None, timestamps=None, current=0, max_len=None):
        self.max_len = check_max_len(max_len)
        self.prices = prices
        self.current = current
        self.timestamps = timestamps

    def current_prices(self):
        return self.prices[:self.current]

    def current_timestamps(self):
        return self.timestamps[:self.current]


class PriceSeries:
    """
        不建议手动创建这个类的实例，
        我们希望全部通过BarDataSeries创建
    """

    def __init__(self, append_event, prices, timestamps, current, max_len):
        self.impl = PriceSeriesImpl(prices, timestamps, current, max_len)

        self.append_event = append_event

    def reset(self, prices=None, timestamps=None, current=0, max_len=None):
        self.impl.reset(prices, timestamps, current, max_len)

    @property
    def prices(self):
        return self.impl.current_prices()

    @property
    def timestamps(self):
        return self.impl.timestamps()


class BarDataSeriesImpl:
    def __init__(self, bars=None, timestamps=None, current=0, max_len=None):

        if max_len is None or max_len <= 0:
            self.max_len = DEFAULT_MAX_LEN
        else:
            self.max_len = max_len
        if bars is not None and current is not None and bars.shape[0] == timestamps.shape[0]:
            self.bars = bars
            self.current = current
            self.timestamps = timestamps
        else:
            self.current = 0
            self.bars = np.zeros((self.max_len, 9), dtype=np.float32)
            self.timestamps = np.zeros(self.max_len, dtype='datetime64[m]')

    def __getitem__(self, key):
        return self.bars[:self.current][key]

    def current_bars(self):
        return self.bars[:self.current]

    def current_timestamps(self):
        return self.timestamps[:self.current]

    def reset(self, max_len=None):
        self.max_len = check_max_len(max_len)
        self.current = 0
        self.bars = np.zeros((max_len, 9), dtype=np.float32)
        self.timestamps = np.zeros(self.max_len, dtype='datetime64[m]')

    def append_with_datetime(self, bar, datetime_):
        """
            DONE:Convert datetime to timestamp
        """

        extended = False

        if self.current == self.max_len:
            self.max_len = self.max_len * 2

            self.bars = np.resize(self.bars, (self.max_len, 9))
            self.timestamps = np.resize(self.timestamps, self.max_len)

            extended = True

        self.bars[self.current] = bar
        self.timestamps[self.current] = datetime_
        self.current += 1

        return extended

    """
        Convert To Single Price series
    """


class BarDataSeries:
    """
        需要获取某个价格序列的时候，直接调用对应的属性即可

        请注意：不要对其进行修改，不然会造成意想不到的后果

        BarDataSeries 会自动对每个分量进行相应的延展。因此你不用考虑可能存在的问题。拿来用就行
    """

    def __init__(self, bars=None, timestamps=None, current=0, max_len=None, frequency=Frequency.MINUTE):
        self.impl = BarDataSeriesImpl(
            bars=bars, timestamps=timestamps, current=current, max_len=max_len)
        self.frequency = frequency

        self.append_event = Event()

        # 这里我们已经将 implement中的相关数据传达了
        # 所以将相应信息交给reset处理即可

        self.ask_open = PriceSeries(self.append_event,
                                    self.impl.bars[:, 0], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_close = PriceSeries(self.append_event,
                                     self.impl.bars[:, 1], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_high = PriceSeries(self.append_event,
                                    self.impl.bars[:, 2], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_low = PriceSeries(self.append_event,
                                   self.impl.bars[:, 3], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_open = PriceSeries(self.append_event,
                                    self.impl.bars[:, 4], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_close = PriceSeries(self.append_event,
                                     self.impl.bars[:, 5], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_high = PriceSeries(self.append_event,
                                    self.impl.bars[:, 6], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_low = PriceSeries(self.append_event,
                                   self.impl.bars[:, 7], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.volume = PriceSeries(self.append_event,
                                  self.impl.bars[:, 8], self.impl.timestamps, self.impl.current, self.impl.max_len)

    def __getitem__(self, key):
        return self.impl[key]

    @property
    def timestamps(self):
        # 截断后的时间戳
        return self.impl.current_timestamps()

    @property
    def bars(self):
        # 截断后的柱状数据
        return self.impl.current_bars()

    def reset(self, max_len=None):
        self.impl.reset(max_len)
        self.__reset_bar_series()

    def __reset_bar_series(self):
        self.ask_open.reset(
            self.impl.bars[:, 0], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_close.reset(
            self.impl.bars[:, 1], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_high.reset(
            self.impl.bars[:, 2], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.ask_low.reset(
            self.impl.bars[:, 3], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_open.reset(
            self.impl.bars[:, 4], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_close.reset(
            self.impl.bars[:, 5], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_high.reset(
            self.impl.bars[:, 6], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.bid_low.reset(
            self.impl.bars[:, 7], self.impl.timestamps, self.impl.current, self.impl.max_len)
        self.volume.reset(
            self.impl.bars[:, 8], self.impl.timestamps, self.impl.current, self.impl.max_len)

    def append(self, bar: Bar):
        """
            利用Bar 内部的序列节约下来序列化的过程
        """

        # 1. 进行追加操作，并判断是否扩充

        extended = self.impl.append_with_datetime(bar.data, bar.start_date)

        # 2. 根据是否有扩充，来判断子列是否扩充

        # 说明：不将此任务放进队列是为了提高效率

        if extended:
            """
                注意，这里当Implement满的时候，BarSeries也重置一下即可。
            """
            self.__reset_bar_series()

        # 3. 再通知我们追加写入了
        self.append_event.emit(extended)

    def as_new(self):
        self.impl.current = 0

    def to_next(self):
        assert self.impl.current != self.impl.max_len

        self.impl.current += 1
        self.append_event.emit(False)

        return self.impl.current < self.impl.max_len
