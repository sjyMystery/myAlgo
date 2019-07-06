import datetime

from myalgo.broker import BackTestBroker
from myalgo.broker import NoCommission
from myalgo.feed import SQLiteFeed
from myalgo.strategy import BackTestStrategy


class Strategy(BackTestStrategy):
    def __init__(self, broker):
        super(Strategy, self).__init__(broker)
        self.__pos = None

    def onEnterOk(self, position):
        self.__pos = position

    def onExitOk(self, position):
        self.__pos = None

    def onBars(self, datetime, bars):

        if self.__pos is None:
            self.enterLong('USDJPY', 10)
        elif not self.__pos.exitActive() and self.__pos.getReturn() > 0:
            self.__pos.exitMarket(True)

    def onFinish(self, bars):
        pass


feed = SQLiteFeed(instruments=['USDJPY'], table_name='bins', file_name='sqlite')
feed.load_data(datetime.date(2012, 1, 1), datetime.date(2013, 1, 1))
broker = BackTestBroker(1000, feed, NoCommission())
strategy = Strategy(broker)

strategy.run()
