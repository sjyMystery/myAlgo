import datetime
import logging

from myalgo.feed import DataFrameFeed
from strategies import orindinary_plus

instrument = 'EURCHF'
p1 = 0.31
p2 = 0.11

start = ('2013-11-01')
end = ('2013-12-01')


# The if __name__ == '__main__' part is necessary if running on Windows.
def main():
    # Load the bar feed from the CSV files.

    start_time = datetime.datetime.now()

    feed = DataFrameFeed(instruments=[instrument],
                         path='ratio.h5', maxLen=24 * 60)
    feed.load_data(start, end)
    s = orindinary_plus.OrindaryStr(feed, p1, p2, instrument)
    s.logger.level = logging.DEBUG
    #
    # plotter = strategyplot.StrategyPlotter(s)
    # plotter.getOrCreateSubplot("returns").addDataSeries(
    #     "simple returns", s.analyzers["ret"].getReturns())
    # plotter.getOrCreateSubplot("cum ret").addDataSeries(
    #     "cum returns", s.analyzers["ret"].getCumulativeReturns())

    s.run()

    end_time = datetime.datetime.now()

    print(end_time - start_time)


if __name__ == '__main__':
    main()
