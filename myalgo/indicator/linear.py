import numpy as np
from scipy import stats

from myalgo import indicator
from myalgo.utils import collections
from myalgo.utils import dt


# Using scipy.stats.linregress instead of numpy.linalg.lstsq because of this:
# http://stackoverflow.com/questions/20736255/numpy-linalg-lstsq-with-big-values
def lsreg(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    res = stats.linregress(x, y)
    return res[0], res[1]


class LinearEventWindow(indicator.EventWindow):
    def __init__(self, windowSize):
        super(LinearEventWindow, self).__init__(windowSize)
        self._timestamps = collections.NumPyDeque(windowSize)

    def onNewValue(self, dateTime, value):
        super(LinearEventWindow, self).onNewValue(dateTime, value)
        if value is not None:
            timestamp = dt.datetime_to_timestamp(dateTime)
            if len(self._timestamps):
                assert (timestamp > self._timestamps[-1])
            self._timestamps.append(timestamp)

    def __getValueAtImpl(self, timestamp):
        ret = None
        if self.windowFull():
            a, b = lsreg(self._timestamps.data(), self.getValues())
            ret = a * timestamp + b
        return ret

    def getValueAt(self, dateTime):
        return self.__getValueAtImpl(dt.datetime_to_timestamp(dateTime))

    def getValue(self):
        ret = None
        if self.windowFull():
            ret = self.__getValueAtImpl(self._timestamps.data()[-1])
        return ret


class Linear(indicator.EventBasedFilter):
    def __init__(self, dataSeries, windowSize, maxLen=None):
        super(Linear, self).__init__(dataSeries, eventWindow=LinearEventWindow(windowSize), maxLen=maxLen)


class SlopeEventWindow(indicator.EventWindow):
    def __init__(self, windowSize):
        super(SlopeEventWindow, self).__init__(windowSize)
        self.__value = None

    def onNewValue(self, dateTime, value):
        super(SlopeEventWindow, self).onNewValue(dateTime, value)
        if value is not None:
            if self.windowFull():
                a, _ = lsreg(range(self.getValues().shape[0]), self.getValues())
                self.__value = a

    def getValue(self):
        return self.__value


class Slope(indicator.EventBasedFilter):
    def __init__(self, dataSeries, windowSize, maxLen=None):
        super(Slope, self).__init__(dataSeries, eventWindow=SlopeEventWindow(windowSize), maxLen=maxLen)
