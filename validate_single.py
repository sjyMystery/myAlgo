import datetime

from myalgo.drawer import strategyplot
from myalgo.feed import SQLiteFeed
from myalgo.stratanalyzer import orderbook
from strategies import orindary


def igen(indicator, *args):
    def I(i):
        return indicator(i, *args)

    return I


instrument = 'EURAUD'
from_date = datetime.date(2014, 1, 1)
to_date = datetime.date(2017, 1, 1)
p1 = 0.62
p2 = 0.23

Book = orderbook.OrderBook()

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=[instrument], table_name='bins', file_name='sqlite')
    feed.load_data(from_date, to_date)
    s = orindary.OrindaryStr(feed, p1, p2, instrument)

    s.attachAnalyzer(Book)
    plotter = strategyplot.StrategyPlotter(s)
    plotter.getOrCreateSubplot("cum ret").addDataSeries("cum returns", s.analyzers["ret"].getCumulativeReturns())
    s.run()

    print(s.effects)
    Book.save_csv('ob1.csv')
    plotter.plot()
