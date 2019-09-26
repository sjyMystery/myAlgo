import logging

from myalgo.drawer import strategyplot
from myalgo.feed import DataFrameFeed
from strategies import orindinary_plus

instrument = 'EURCHF'
p1 = 0.31
p2 = 0.11

start = ('2012-01-01')
end = ('2012-12-01')

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = DataFrameFeed(instruments=[instrument],
                         path='ratio.h5')
    feed.load_data(start, end)
    s = orindinary_plus.OrindaryStr(feed, p1, p2, instrument)
    s.logger.level = logging.DEBUG

    plotter = strategyplot.StrategyPlotter(s)
    plotter.getOrCreateSubplot("returns").addDataSeries(
        "simple returns", s.analyzers["ret"].getReturns())
    plotter.getOrCreateSubplot("cum ret").addDataSeries(
        "cum returns", s.analyzers["ret"].getCumulativeReturns())

    s.run()
    plotter.plot()
    plotter.savePlot(f'./result_image/curve-{instrument}.png')
