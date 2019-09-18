from myalgo import indicator
from myalgo.indicator import ma


class TrendEventWindow(ma.SMAEventWindow):
    def __init__(self, period, short_period):
        assert (period > 0)
        super(TrendEventWindow, self).__init__(period)
        self.__value = None
        self.__period = period
        self.__short_period = short_period

    def onNewValue(self, dateTime, value):
        super(TrendEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            first = self.getValues()[0:self.__short_period].mean()
            last = self.getValues()[-self.__short_period:].mean()
            self.__value = (last - first) / self.__period

    def getValue(self):
        return self.__value


class Trend(indicator.EventBasedFilter):
    """
        我们用一个长周期和一个短周期来描述趋势
        用长周期头部和尾部短周期长度的平均值的变化速率来表现
        :param dataSeries
        :type dataSeries:myalgo.dataseries.DataSeries
        :param longPeriod: 长周期
        :type longPeriod:int
        :param shortPeriod: 短周期
        :type shortPeriod:int
        :param maxLen
        :type maxLen:Int

    """

    def __init__(self, dataSeries, longPeriod, shortPeriod, maxLen=None):
        assert longPeriod > shortPeriod, "longPeriod should be longer than the shorter one"

        super(Trend, self).__init__(dataSeries, TrendEventWindow(longPeriod, shortPeriod), maxLen)
