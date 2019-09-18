import datetime

from myalgo.feed import SQLiteFeed
from strategies import orindary

instrument = 'EURCHF'
from_date = datetime.date(2012, 1, 1)
to_date = datetime.date(2013, 1, 1)
p1 = 0.31
p2 = 0.11
# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=[instrument], table_name='bins', file_name='sqlite')
    feed.load_data(from_date, to_date)
    s = orindary.OrindaryStr(feed, p1, p2, instrument)

    s.run()
