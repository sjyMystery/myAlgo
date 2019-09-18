import pandas as pd

from myalgo import stratanalyzer
from myalgo.logger import get_logger
from myalgo.order import Order


class OrderBook(stratanalyzer.StrategyAnalyzer):
    l = get_logger('OrderBook')

    def to_df(self):

        self.l.debug('Converting The Order Book...')

        positions = []
        for position in self.strat.positions:
            dict = {
                "instrument": None,
                "return": None,
                "PnL": None,
                "entry_state": None,
                "entry_type": None,
                "entry_fill_price": None,
                "entry_amounts": None,
                "entry_filled": None,
                "entry_submitted_at": None,
                "entry_accepted_at": None,
                "entry_finished_at": None,
                "entry_canceled_at": None,
                "exit_state": None,
                "exit_type": None,
                "exit_fill_price": None,
                "exit_submitted_at": None,
                "exit_accepted_at": None,
                "exit_finished_at": None,
                "exit_canceled_at": None,
                "exit_amounts": None,
                "exit_filled": None,
                "not_filled": None,
            }
            entry_order: Order = position.getEntryOrder()
            dict["instrument"] = position.getInstrument()
            dict["entry_state"] = entry_order.state
            dict["amounts"] = position.getAmounts()
            dict["entry_submitted_at"] = entry_order.submitted_at
            dict["entry_accepted_at"] = entry_order.accepted_at
            dict["entry_finished_at"] = entry_order.finish_datetime
            dict["entry_canceled_at"] = entry_order.canceled_at
            dict["entry_type"] = entry_order.type
            dict["entry_amounts"] = entry_order.quantity
            dict["entry_filled"] = entry_order.filled
            if entry_order.is_filled:
                dict["entry_fill_price"] = position.getEntryOrder().avg_fill_price

            exit_order: Order = position.getExitOrder()

            if exit_order is not None:
                dict["exit_submitted_at"] = exit_order.submitted_at
                dict["exit_accepted_at"] = exit_order.accepted_at
                dict["exit_canceled_at"] = exit_order.canceled_at
                dict["exit_finished_at"] = exit_order.finish_datetime
                dict["exit_type"] = exit_order.type
                dict["exit_state"] = exit_order.state
                dict["exit_amounts"] = exit_order.quantity
                dict["exit_filled"] = exit_order.filled
                if exit_order.is_filled:
                    dict["exit_fill_price"] = exit_order.avg_fill_price

            dict["not_filled"] = position.getAmounts()
            dict["PnL"] = position.getPnL()
            dict["return"] = position.getReturn()

            positions.append(dict)

        dict = {
            "instrument": None,
            "return": None,
            "PnL": None,
            "entry_state": None,
            "entry_type": None,
            "entry_fill_price": None,
            "entry_amounts": None,
            "entry_filled": None,
            "entry_submitted_at": None,
            "entry_accepted_at": None,
            "entry_finished_at": None,
            "entry_canceled_at": None,
            "exit_state": None,
            "exit_type": None,
            "exit_fill_price": None,
            "exit_submitted_at": None,
            "exit_accepted_at": None,
            "exit_finished_at": None,
            "exit_canceled_at": None,
            "exit_amounts": None,
            "exit_filled": None,
            "not_filled": None,
        }

        df = pd.DataFrame(positions, columns=dict.keys())

        return df

    def save_csv(self, filename):

        return self.to_df().to_csv(filename)
