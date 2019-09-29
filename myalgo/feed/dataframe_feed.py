import numpy as np
import pandas as pd

from myalgo.bar.bar import Bar, Frequency
from myalgo.feed.barfeed import BaseBarFeed
from myalgo.logger import get_logger


class HistoryStore:
    def __init__(self, filename):
        self.store = pd.HDFStore(filename)
        self.instruments = list(
            map(lambda x: x.replace('/', ''), self.store.keys()))
        self.histories = {}

    def read(self, instrument):
        if instrument in self.instruments:
            df: pd.DataFrame = self.store.get(instrument)
            history = History(df, instrument)
            self.histories[instrument] = history
            return self.histories[instrument]
        return None

    def read_all(self):
        for instrument in self.instruments:
            self.read(instrument)

    def __getitem__(self, item):
        return self.histories[item]


class History:
    def __init__(self, df, instrument, n_partitions=100):
        self.df: pd.DataFrame = df
        self.instrument = instrument

    def feed(self, n_partitions=100):
        return DataFrameFeed.from_history(self, n_partitions=n_partitions)


class DataFrameFeed(BaseBarFeed):
    def __init__(self, path, instruments, frequency=Frequency.MINUTE, maxLen=None):

        super(DataFrameFeed, self).__init__(frequency, instruments, None, maxLen)

        self.store = pd.HDFStore(path)

        self.__logger = get_logger("DATAFrameFeed Logger")

    def load_data(self, start, end):
        instruments = self.instruments

        self.__logger.debug(
            f'loading data from HDFStore, for instruments: {instruments}')
        data_dicts = {}

        length = []

        for instrument in instruments:
            df = self.store.get(instrument)

            df = df[start:end]

            records = df.to_records()

            data_dicts[instrument] = np.array(records).flat
            length.append(len(data_dicts[instrument]))

        self.__logger.info('loading data from HDFStore complete!')

        m_length = min(length)

        def get_instrument(i):
            new_dicts = {}
            for inst in instruments:
                t, bo, bh, bl, bc, ao, ah, al, ac = data_dicts[inst][i]
                t = np.datetime64(t, 'm')
                new_dicts[inst] = Bar.from_bar(t, t + self.frequency, ao, ac, ah, al,
                                               bo, bc, bh, bl, 0)
            return new_dicts

        result = [get_instrument(i) for i in range(m_length)]

        self.__logger.info('converting data complete!')

        self.bars = result
