from myalgo.bar.bars import Bars
from myalgo.config import dispatchprio
from myalgo.dataseries import bards
from myalgo.event import Event
from myalgo.feed import basefeed

class BaseBarFeed(basefeed.BaseFeed):
    def __init__(self, frequency, instruments, bars=None, maxLen=None):

        self.__bars = bars if bars is not None else []
        self.__bar_len = len(self.__bars)

        self.__bar_events = Event()
        self.__feed_reset_event = Event()

        self.__current_bar_index = 0

        self.__started = False
        self.__frequency = frequency

        self.__useAdjustedValues = None
        self.__defaultInstrument = None

        super(BaseBarFeed, self).__init__(maxLen)

        self.__instruments = instruments

        for instrument in instruments:
            self.register_instrument(instrument)

        try:
            self.__barsHaveAdjClose = self.__bars[0][instruments[0]].getAdjClose() is not None
        except Exception:
            self.__barsHaveAdjClose = False

    def reset(self):
        self.__started = False
        self.__current_bar_index = 0
        self.__feed_reset_event.emit(self.__bars)

    def clone(self):
        new_feed = BaseBarFeed(bars=self.bars, maxLen=self.max_len, frequency=self.__frequency,
                               instruments=self.__instruments)
        return new_feed

    @property
    def bar_events(self):
        return self.__bar_events

    @property
    def pos(self):
        return self.__current_bar_index

    @property
    def bars(self):
        return self.__bars

    @property
    def current_bars(self):
        """

        :return:
        """
        if self.__current_bar_index >= self.__bar_len:
            return None

        return self.bars[self.__current_bar_index]

    @property
    def next_bars(self):
        self.__current_bar_index += 1
        now = self.current_bars
        return now

    @property
    def current_datetime(self):
        return self.current_bars.datetime if self.current_bars else None

    @property
    def last_bars(self):
        return self.__bars[self.pos - 1] if self.pos > 0 and self.__current_bar_index < self.__bar_len + 1 else None

    def last_bar(self, instrument):
        return self.last_bars.bar(instrument) if self.last_bars is not None else None

    def start(self):
        super(BaseBarFeed, self).start()
        self.__started = True

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        return self.__current_bar_index + 1 >= self.__bar_len

    def peek_datetime(self):
        return self.current_datetime

    def dispatch(self):
        current_datetime, current_bars = self.getNextValuesAndUpdateDS()
        if current_bars is not None:
            self.__bar_events.emit(current_datetime, self.last_bars, self.current_bars)
        return current_bars is not None

    @bars.setter
    def bars(self, value):
        self.__bars = [Bars(bar_dict=i) for i in value]
        self.__bar_len = len(self.__bars)
        self.__current_bar_index = 0
        self.__started = False
        self.__feed_reset_event.emit(self.__bars)

    @property
    def instruments(self):
        """
            暂时我们只认第一个
        :return:
        """
        return self.__instruments

    @property
    def feed_reset_event(self):
        return self.__feed_reset_event

    def createDataSeries(self, key, maxLen):
        ret = bards.BarDataSeries(maxLen)
        ret.setUseAdjustedValues(self.__useAdjustedValues)
        return ret

    @property
    def registered_instruments(self):
        """Returns a list of registered intstrument names."""
        return self.getKeys()

    def register_instrument(self, instrument):
        self.__defaultInstrument = instrument
        self.registerDataSeries(instrument)

    @property
    def default_instrument(self):
        return self.__defaultInstrument

    def data_series(self, instrument=None):
        """Returns the :class:`pyalgotrade.dataseries.bards.BarDataSeries` for a given instrument.

        :param instrument: Instrument identifier. If None, the default instrument is returned.
        :type instrument: string.
        :rtype: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
        """
        if instrument is None:
            instrument = self.__defaultInstrument
        return self[instrument]

    def dispatch_priority(self):
        return dispatchprio.BAR_FEED

    def set_use_adjusted_values(self, use_adjusted):
        if use_adjusted and not self.bars_have_adj_close:
            raise Exception("The barfeed doesn't support adjusted close values")
        # This is to affect future dataseries when they get created.
        self.__useAdjustedValues = use_adjusted
        # Update existing dataseries
        for instrument in self.registered_instruments():
            self[instrument].setUseAdjustedValues(use_adjusted)

    @property
    def next_values(self):
        values = self.next_bars
        return self.current_datetime, values

    @property
    def bars_have_adj_close(self):
        return self.__barsHaveAdjClose

    @property
    def frequency(self):
        return self.__frequency


# This class is used by the optimizer module. The barfeed is already built on the server side,
# and the bars are sent back to workers.
class OptimizerBarFeed(BaseBarFeed):

    def __init__(self, frequency, instruments, bars, maxlen=None):
        super(OptimizerBarFeed, self).__init__(frequency, instruments=instruments, bars=bars, maxLen=maxlen)
