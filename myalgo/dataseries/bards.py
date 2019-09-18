import six

from myalgo import dataseries


class BarDataSeries(dataseries.SequenceDataSeries):
    """A DataSeries of :class:`pyalgotrade.bar.Bar` instances.

    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, maxLen=None):
        super(BarDataSeries, self).__init__(maxLen)
        self.__ask_open = dataseries.SequenceDataSeries(maxLen)
        self.__ask_close = dataseries.SequenceDataSeries(maxLen)
        self.__bid_open = dataseries.SequenceDataSeries(maxLen)
        self.__bid_close = dataseries.SequenceDataSeries(maxLen)
        self.__ask_high = dataseries.SequenceDataSeries(maxLen)
        self.__ask_low = dataseries.SequenceDataSeries(maxLen)
        self.__bid_high = dataseries.SequenceDataSeries(maxLen)
        self.__bid_low = dataseries.SequenceDataSeries(maxLen)
        self.__volumeDS = dataseries.SequenceDataSeries(maxLen)
        self.__adjCloseDS = dataseries.SequenceDataSeries(maxLen)
        self.__extraDS = {}
        self.__useAdjustedValues = False

    def __getOrCreateExtraDS(self, name):
        ret = self.__extraDS.get(name)
        if ret is None:
            ret = dataseries.SequenceDataSeries(self.getMaxLen())
            self.__extraDS[name] = ret
        return ret

    def setUseAdjustedValues(self, useAdjusted):
        self.__useAdjustedValues = useAdjusted

    def append(self, bar):
        self.appendWithDateTime(bar.start_date, bar)

    def appendWithDateTime(self, dateTime, bar):
        assert (dateTime is not None)
        assert (bar is not None)
        bar.set_use_adjusted_values(self.__useAdjustedValues)

        super(BarDataSeries, self).appendWithDateTime(dateTime, bar)

        self.__ask_high.appendWithDateTime(dateTime, bar.ask_high)
        self.__ask_low.appendWithDateTime(dateTime, bar.ask_low)
        self.__ask_open.appendWithDateTime(dateTime, bar.ask_open)
        self.__ask_close.appendWithDateTime(dateTime, bar.ask_close)
        self.__bid_high.appendWithDateTime(dateTime, bar.bid_high)
        self.__bid_low.appendWithDateTime(dateTime, bar.bid_low)
        self.__bid_open.appendWithDateTime(dateTime, bar.bid_open)
        self.__bid_close.appendWithDateTime(dateTime, bar.bid_close)
        self.__volumeDS.appendWithDateTime(dateTime, bar.volume)




        # Process extra columns.
        for name, value in six.iteritems(bar.extra_columns):
            extraDS = self.__getOrCreateExtraDS(name)
            extraDS.appendWithDateTime(dateTime, value)

    @property
    def volume(self):
        return self.__volumeDS

    @property
    def ask_high(self):
        return self.__ask_high

    @property
    def ask_low(self):
        return self.__ask_low

    @property
    def ask_open(self):
        return self.__ask_open

    @property
    def ask_close(self):
        return self.__ask_close

    @property
    def bid_high(self):
        return self.__bid_high

    @property
    def bid_low(self):
        return self.__bid_low

    @property
    def bid_open(self):
        return self.__bid_open

    @property
    def bid_close(self):
        return self.__bid_close

    @property
    def price(self):
        return self.bid_close
