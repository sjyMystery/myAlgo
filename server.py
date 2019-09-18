import datetime
import itertools
import logging

import numpy as np

import strategies.orindary
from myalgo.feed import SQLiteFeed
from myalgo.optimizer import local


def parameters_generator():
    p1 = np.arange(0.0, 0.2, 0.0005)
    p2 = np.arange(0.0, 0.01, 0.001)
    return itertools.product(p1, p2, ['USDJPY'])


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=['USDJPY'], table_name='bins', file_name='sqlite')
    feed.load_data(datetime.date(2015, 1, 1), datetime.date(2016, 1, 1))
    # Run the server.
    local.run(strategies.orindary.OrindaryStr, feed, parameters_generator(), batchSize=2, workerCount=36,
              logLevel=logging.DEBUG)
