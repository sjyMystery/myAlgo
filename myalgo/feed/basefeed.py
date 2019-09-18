import abc

from myalgo import dataseries
from myalgo.event import Event, Subject


def feed_iterator(feed):
    feed.start()
    try:
        while not feed.eof():
            yield feed.getNextValuesAndUpdateDS()
    finally:
        feed.stop()
        feed.join()


class BaseFeed(Subject):
    """Base class for feeds.

    :param maxLen: The maximum number of values that each :class:`pyalgotrade.dataseries.DataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, maxLen):
        super(BaseFeed, self).__init__()

        maxLen = dataseries.get_checked_max_len(maxLen)

        self.__ds = {}
        self.__event = Event()
        self.__maxLen = maxLen

    @property
    def max_len(self):
        return self.__maxLen

    def reset(self):
        keys = list(self.__ds.keys())
        self.__ds = {}
        for key in keys:
            self.registerDataSeries(key)

    # Subclasses should implement this and return the appropriate dataseries for the given key.
    @abc.abstractmethod
    def createDataSeries(self, key, maxLen):
        raise NotImplementedError()

    # Subclasses should implement this and return a tuple with two elements:
    # 1: datetime.datetime.
    # 2: dictionary or dict-like object.
    @property
    @abc.abstractmethod
    def next_values(self):
        raise NotImplementedError()

    def registerDataSeries(self, key):
        if key not in self.__ds:
            self.__ds[key] = self.createDataSeries(key, self.__maxLen)

    def getNextValuesAndUpdateDS(self):
        dateTime, values = self.next_values
        if dateTime is not None:
            for key, value in values.items:
                # Get or create the datseries for each key.
                try:
                    ds = self.__ds[key]
                except KeyError:
                    ds = self.createDataSeries(key, self.__maxLen)
                    self.__ds[key] = ds
                """
                    这里key,value对应于上层分别是种类和Feed的填充物，比如instrument和Bar
                    整个循环把Feed里面所有种类的每一项加到DS后面去
                """
                ds.appendWithDateTime(dateTime, value)
        return dateTime, values

    def __iter__(self):
        return feed_iterator(self)

    def getNewValuesEvent(self):
        """Returns the event that will be emitted when new values are available.
        To subscribe you need to pass in a callable object that receives two parameters:

         1. A :class:`datetime.datetime` instance.
         2. The new value.
        """
        return self.__event

    def dispatch(self):
        dateTime, values = self.getNextValuesAndUpdateDS()
        if dateTime is not None:
            self.__event.emit(dateTime, values)
        return dateTime is not None

    def getKeys(self):
        return list(self.__ds.keys())

    def __getitem__(self, key):
        return self.__ds[key]

    def __contains__(self, key):
        return key in self.__ds
