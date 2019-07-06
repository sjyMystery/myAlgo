import datetime
import itertools

from myalgo.feed import SQLiteFeed
from myalgo.optimizer import server


def parameters_generator():
    instrument = ["ibm"]
    entrySMA = range(150, 251)
    exitSMA = range(5, 16)
    rsiPeriod = range(2, 11)
    overBoughtThreshold = range(75, 96)
    overSoldThreshold = range(5, 26)
    return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=['USDJPY'], table_name='bins', file_name='sqlite')
    feed.load_data(datetime.date(2012, 1, 1), datetime.date(2012, 2, 1))

    # Run the server.
    server.serve(feed, parameters_generator(), "localhost", 5000)
