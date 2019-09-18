import datetime

from myalgo.drawer import strategyplot
from myalgo.feed import SQLiteFeed
from strategies import orindinary_plus

instrument = 'EURCHF'
from_date = datetime.date(2012, 1, 1)
to_date = datetime.date(2014, 1, 1)
p1 = 0.31
p2 = 0.11
# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=[instrument], table_name='bins', file_name='sqlite')
    feed.load_data(from_date, to_date)
    s = orindinary_plus.OrindaryStr(feed, p1, p2, instrument)

    plotter = strategyplot.StrategyPlotter(s)
    plotter.getOrCreateSubplot("returns").addDataSeries("simple returns", s.analyzers["ret"].getReturns())
    plotter.getOrCreateSubplot("cum ret").addDataSeries("cum returns", s.analyzers["ret"].getCumulativeReturns())

    s.run()
    plotter.plot()
    plotter.savePlot(f'./result_image/curve-{instrument}.png')
