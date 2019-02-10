import strategy
import broker.backtest
import feed
import broker.commission
import datetime
import pandas as pd
import numpy as np
import time

class MyStrategy(strategy.BaseStrategy):

    def __init__(self, broker):
        super(MyStrategy, self).__init__(broker)
        self.history = []
        self.positions = []

        self.use_event_datetime_logs = True

        self.consume = 0

    def history_df(self, start):
        return pd.DataFrame([bar.dict for bar in self.history[start:]])

    def onBars(self, dateTime, bars):
        # self.enterLongLimit('USDJPY', 87.8, 100)

        start = time.time()

        bar = bars['USDJPY']

        self.history.append(bar)
        history_df = self.history_df(-10)
        if len(self.history) >=10:
            bid_highs = np.array(history_df.loc[:, "bid_high"])
            x = np.array(range(10))


            reg = np.polyfit(x, bid_highs, 1)

            if reg[0]>0:

                quantity = int((self.broker.cash() * 0.9) / bar.ask_close)
                if quantity > 10:
                    position = self.enterLong('USDJPY',quantity)
                    self.positions.append(position)

        exit_his_length = 60
        history_max = self.history_df(-exit_his_length)
        bid_highs_max = np.array(history_max.loc[:, "bid_high"])

        for position in self.positions:
            if position.entryFilled() and not position.exitActive():
                if bar.out_price >= position.getEntryOrder().avg_fill_price*1.0001:
                    position.exitMarket()
                elif bar.out_price <= position.getEntryOrder().avg_fill_price*0.990:
                    position.exitStop(position.getEntryOrder().avg_fill_price*0.990)
                else:
                    if len(self.history)>exit_his_length:
                        x_max = np.array(range(exit_his_length))
                        reg_max = np.polyfit(x_max, bid_highs_max, 1)
                        if reg_max[0]<0:
                            if bar.out_price > position.getEntryOrder().avg_fill_price:
                                position.exitMarket()
                            elif bar.out_price <= position.getEntryOrder().avg_fill_price*0.995:
                                position.exitMarket()
        end = time.time()

        self.consume += end-start


    def onEnterOk(self, position):
        super().onEnterOk(position)

    def onEnterCanceled(self, position):
        super().onEnterCanceled(position)

    def onExitOk(self, position):
        super().onExitOk(position)

        exit_order = position.getExitOrder()


    def onExitCanceled(self, position):
        super().onExitCanceled(position)

    def onStart(self):
        super().onStart()

    def onFinish(self, bars):
        super().onFinish(bars)

        self.logger.info(self.broker.equity)

    def onIdle(self):
        super().onIdle()

    def onOrderUpdated(self, order):
        super().onOrderUpdated(order)

        self.logger.info(f'cash:{self.broker.cash()} eq:{self.broker.equity} thinking consume:{self.consume}')


bar_feed = feed.DBFeed(table_name='bins', db_password='123456')

bar_feed.load_data(['USDJPY'], datetime.datetime(2018, 1, 1, 0, 0, 0), datetime.datetime(2019, 1, 1, 0, 0, 0))

backtest = broker.backtest.BackTestBroker(100000, bar_feed, broker.commission.NoCommission())

my = MyStrategy(backtest)

my.run()
