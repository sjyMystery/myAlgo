import math

from myalgo import indicator
from myalgo.indicator import ma


class VolatilityEventWindow(ma.SMAEventWindow):
    def __init__(self, period):
        assert (period > 0)
        super(VolatilityEventWindow, self).__init__(period)
        self.__value = None
        self.__period = period

    def onNewValue(self, dateTime, value):
        super(VolatilityEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            try:
                self.__value = math.log(self.getValues()[-1]) - math.log(self.getValues()[0])
            except Exception as e:
                self.__value = None
            finally:
                pass

    def getValue(self):
        return self.__value


class Volatility(indicator.EventBasedFilter):
    def __init__(self, dataSeries, longPeriod, maxLen=None):
        super(Volatility, self).__init__(dataSeries, VolatilityEventWindow(longPeriod), maxLen)
