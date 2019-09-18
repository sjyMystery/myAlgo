from datetime import timedelta
from queue import Queue

from myalgo import strategy
from myalgo.broker import NoCommission
from myalgo.indicator import highlow


class OrindaryStr(strategy.BackTestStrategy):
    def __init__(self, feed, p1, p2, instrument):
        super(OrindaryStr, self).__init__(feed, 10000, round=lambda x: int(x), commission=NoCommission())

        self.stop_rate = 0.50

        self.__instrument = instrument
        self.__priceDS = feed[instrument].price
        self.__high = highlow.High(self.__priceDS, 60 * 24)
        self.__low = highlow.Low(self.__priceDS, 60 * 24)
        self.__p1 = p1
        self.__p2 = p2
        self.__pos = None

        self.__buy_in_queue = Queue()

        # self.__positions = []

        # 是否正在止损
        self.__stopping = False

        self.__unusable = 1000

    def onEnterCanceled(self, position):
        self.__pos = None
        self.__stopping = False
        if not self.__buy_in_queue.empty():
            enter_price = self.__buy_in_queue.get()
            self.__enter(enter_price)

    def onExitOk(self, position):
        # self.__positions.append(position)
        self.__pos = None
        self.__stopping = False

    def onExitCanceled(self, position):
        # 赶紧跑路，不然GG
        position.exitMarket(True)

    def onEnterOk(self, position):
        position.exitLimit(position.getEntryOrder().avg_fill_price + self.__range * self.__p2,
                           True)

    def onBars(self, datetime, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        if self.__high[-1] is None or self.__low[-1] is None:
            return

        if self.isPeriodStart(datetime):
            # if self.__vol is not None and self.__vol[-1] <= 0:
            self.enterPeriod(bars)

        if self.__pos is not None and not self.__stopping:
            # 这表明位置已经建立，但是没有被强行平仓，那么考虑强行平仓的可能性
            if self.timeOut(datetime) or (self.__pos.entryFilled() and self.stopHit(bars)):
                self.Exit()

    """
        只需要判断是不是4小时的周期开始
    """

    def isPeriodStart(self, datetime):
        if datetime.hour % 4 is 0 and datetime.minute is 0 and datetime.second is 0:
            return True
        else:
            return False

    def Exit(self):
        self.__stopping = True
        # 进去了就取消退出，然后马上挂市价单滚犊子。
        # 没进去就直接不要进去了，滚回来

        if self.__pos.entryFilled():
            self.__pos.cancelExit()
        else:
            self.__pos.cancelEntry()

    def timeOut(self, datetime):
        return datetime - self.__pos.getEntryOrder().submitted_at > timedelta(hours=3, minutes=55)

    def stopHit(self, bars):

        return bars[
                   self.__instrument].out_price <= self.__pos.getEntryOrder().avg_fill_price - self.stop_rate * self.__range

    def enterPeriod(self, bars):
        """
            显著的问题是，其实并不好处理，如果上一次的条件仍然没有达到的话。
        :param bars:
        :return:
        """
        price = bars[self.__instrument].in_price
        self.__range = (self.__high[-1] - self.__low[-1])
        enter_price = price - self.__range * self.__p1

        if self.__pos is not None:
            #  当前仓位不是空的时候，不允许做任何的买入操作

            return

        self.__enter(enter_price)

    def __enter(self, price):
        if self.usable_cash < 0:
            return
        quantity = int(self.usable_cash / price)

        self.__pos = self.enterLongLimit(self.__instrument, price, quantity, True)

    @property
    def usable_cash(self):
        return self.broker.cash() - self.__unusable
