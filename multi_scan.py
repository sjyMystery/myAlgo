import datetime
import itertools
import logging

import strategies.orindary
from myalgo.drawer.resultDrawer import ResultDrawer
from myalgo.feed import SQLiteFeed
from myalgo.optimizer import local
from myalgo.optimizer.results import ResultManager

instruments = [
    # "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPCHF",
    "GBPJPY",
    "GBPNZD",
    "GBPUSD",
    "NZDCAD",
    "NZDCHF",
    "NZDJPY",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "USDJPY"]


def parameters_generator(instrument):
    a = [0.31]
    p2 = [0.11]
    return itertools.product(a, p2, [instrument])


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.

    for instrument in instruments:
        feed = SQLiteFeed(instruments=[instrument], table_name='bins', file_name='sqlite')
        feed.load_data(datetime.datetime(2014, 1, 1, 20, 25), datetime.datetime(2017, 1, 1, 20, 25))
        local.run(strategies.orindary.OrindaryStr, feed, parameters_generator(instrument), batchSize=2,
                  logLevel=logging.DEBUG, result_file=f"result_data/{instrument}.sqlite", workerCount=30)
    for instrument in instruments:
        # now draw curves
        result = ResultManager('BackTestStrategy', file_name=f"result_data/{instrument}.sqlite")
        data = result.load()
        drawer = ResultDrawer(data)
        drawer.draw_lines(f'./result_image/{instrument}-line.png')
