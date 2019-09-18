from myalgo import strategy
from myalgo.broker import NoCommission
from myalgo.indicator import ma, rsi, cross


class RSI2(strategy.BackTestStrategy):
    def __init__(self, feed, p1, p2, instrument):
        super(RSI2, self).__init__(feed, 10000, round=lambda x: int(x), commission=NoCommission())
        self.__instrument = instrument
        self.__priceDS = feed[instrument].price
        self.__entrySMA = ma.SMA(self.__priceDS, 240)
        self.__exitSMA = ma.SMA(self.__priceDS, 240)
        self.__rsi = rsi.RSI(self.__priceDS, 240)
        self.__p1 = p1
        self.__p2 = p2
        self.__longPos = None
        self.__shortPos = None

    def getEntrySMA(self):
        return self.__entrySMA

    def getExitSMA(self):
        return self.__exitSMA

    def getRSI(self):
        return self.__rsi

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert (False)

    def onExitOk(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert (False)

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def onBars(self, datetime, bars, ):
        # Wait for enough bars to be available to calculate SMA and RSI.
        if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
            return

        bar = bars[self.__instrument]
        if self.__longPos is not None:
            if self.exitLongSignal():
                self.__longPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                shares = int(self.broker.cash() * 0.9 / bars[self.__instrument].price)
                self.__longPos = self.enterLong(self.__instrument, shares, True)

    def enterLongSignal(self, bar):
        return bar.price <= self.__entrySMA[-1] and self.__rsi[-1] <= self.__p1

    def exitLongSignal(self):
        return (cross.cross_above(self.__priceDS, self.__exitSMA) or self.__rsi[
            -1] >= self.__p2) and not self.__longPos.exitActive()
