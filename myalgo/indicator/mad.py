from myalgo import indicator
from myalgo.indicator import ma


class SMADEventWindow(ma.SMAEventWindow):
    def __init__(self, period):
        assert (period > 0)
        super(SMADEventWindow, self).__init__(period)
        self.__value = None

    def onNewValue(self, dateTime, value):
        super(SMADEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            mean_value = super(SMADEventWindow, self).getValue()

            self.__value = (value - mean_value) / mean_value * 100

    def getValue(self):
        return self.__value


class SMAD(indicator.EventBasedFilter):
    def __init__(self, dataSeries, period, maxLen=None):
        super(SMAD, self).__init__(dataSeries, SMADEventWindow(period), maxLen)


class SMADRangeEventWindow(ma.SMAEventWindow):
    def __init__(self, period):
        assert (period > 0)
        super(SMADRangeEventWindow, self).__init__(period)
        self.__value = None

    def onNewValue(self, dateTime, value):
        super(SMADRangeEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            mean_value = super(SMADRangeEventWindow, self).getValue()
            self.__value = (value - mean_value) / (self.getValues().max() - self.getValues().min()) * 100

    def getValue(self):
        return self.__value


class SMADRange(indicator.EventBasedFilter):
    def __init__(self, dataSeries, period, maxLen=None):
        super(SMADRange, self).__init__(dataSeries, SMADRangeEventWindow(period), maxLen)
