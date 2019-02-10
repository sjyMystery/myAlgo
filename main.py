import strategy
import broker.backtest
import feed
import broker.commission
import datetime
import pandas as pd


class MyStrategy(strategy.BaseStrategy):

    def __init__(self, broker):
        super(MyStrategy, self).__init__(broker)
        self.history = []
        self.positions = []

        self.use_event_datetime_logs = True

    def history_df(self, start, end):
        return pd.DataFrame([bar.dict for bar in self.history[start:end]]) if len(self.history) >= end - start else None

    def onBars(self, dateTime, bars):
        # self.enterLongLimit('USDJPY', 87.8, 100)

        bar = bars['USDJPY']

        self.history.append(bar)
        history_df = self.history_df(-21, -1)
        if history_df is not None:
            if bar.ask_close <= history_df.loc[:, "ask_low"].min():

                quantity = int(self.broker.cash() / bar.ask_close)
                if quantity > 1:
                    self.logger.info(f'trying to enter at:{bar.ask_close}')
                    position = self.enterLongLimit('USDJPY', bar.ask_close, quantity - 1)
                    self.positions.append(position)

    def onEnterOk(self, position):
        super().onEnterOk(position)
        entry_order = position.getEntryOrder()
        position.exitLimit(entry_order.price * 1.0001, goodTillCanceled=True)
        self.logger.info(f'enter:{entry_order}')

    def onEnterCanceled(self, position):
        super().onEnterCanceled(position)

    def onExitOk(self, position):
        super().onExitOk(position)

        exit_order = position.getExitOrder()

        self.logger.info(f'exit:{exit_order}')

        self.logger.info(f'cash:{self.broker.cash()} eq:{self.broker.equity}')

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

        self.logger.info(order)
        self.logger.info(self.broker.equity)


bar_feed = feed.DBFeed(table_name='bins', db_password='123456')

bar_feed.load_data(['USDJPY'], datetime.datetime(2013, 1, 1, 0, 0, 0), datetime.datetime(2014, 1, 1, 0, 0, 0))

backtest = broker.backtest.BackTestBroker(100000, bar_feed, broker.commission.NoCommission())

my = MyStrategy(backtest)

my.run()
