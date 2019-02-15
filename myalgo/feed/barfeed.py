from myalgo.bar.bars import Bars
from myalgo.event import Event, Subject


class BarFeed(Subject):
    def __init__(self, bars=[]):

        self.__bars = bars

        self.__bar_events = Event()
        self.__feed_reset_event = Event()

        self.__current_bar_index = 0

        self.__started = False

        super(BarFeed, self).__init__()

    def reset(self):
        self.__started = False
        self.__current_bar_index = 0
        self.__feed_reset_event.emit(self.__bars)

    def clone(self):
        new_feed = BarFeed(bars=self.bars)
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
        if self.__current_bar_index >= len(self.bars):
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
        return self.bars[self.pos - 1] if self.pos > 0 and self.__current_bar_index < len(self.bars) + 1 else None

    def last_bar(self, instrument):
        return self.last_bars.bar(instrument) if self.last_bars is not None else None

    def start(self):
        super(BarFeed, self).start()
        self.__started = True

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        return self.__current_bar_index >= len(self.bars)

    def peek_datetime(self):
        return self.current_datetime

    def dispatch(self):
        current_bars = self.next_bars
        if current_bars is not None:
            self.__bar_events.emit(current_bars.datetime, self.last_bars, self.current_bars)
        return current_bars is not None

    @bars.setter
    def bars(self, value):
        self.__bars = [Bars(bar_dict=i) for i in value]
        self.__current_bar_index = 0
        self.__started = False
        self.__feed_reset_event.emit(self.__bars)

    @property
    def instruments(self):
        """
            暂时我们只认第一个
        :return:
        """
        return self.__bars[0].instruments if len(self.__bars) > 0 else []

    @property
    def feed_reset_event(self):
        return self.__feed_reset_event
