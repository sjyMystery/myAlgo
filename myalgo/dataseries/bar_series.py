import numpy as np

from numba import jitclass, int32, float32, int64,jit


DEFAULT_MAX_LEN = 30000000


@jit(int32(int32))
def check_max_len(max_len):
    if max_len is None or max_len <= 0:
        return DEFAULT_MAX_LEN
    else:
        return max_len


bar_series_class = [
    ("max_len", int64),
    ("current", int64),
    ("bars", float32[:, :]),
    ("timestamps", float32[:])
]


@jitclass(bar_series_class)
class BarDataSeries:
    def __init__(self, bars=None, timestamps=None, current=None, max_len=None):

        if max_len is None or max_len <= 0:
            self.max_len = DEFAULT_MAX_LEN
        else:
            self.max_len = max_len
        if bars is not None and current is not None and bars.shape[0] == timestamps.shape[0]:
            self.bars = bars
            self.current = current
            self.timestamps = timestamps
        else:
            self.current = 0
            self.bars = np.zeros((self.max_len, 9), dtype=np.float32)
            self.timestamps = np.zeros((self.max_len), dtype=np.float32)

    def __getitem__(self, key):
        return self.bars[key]

    def reset(self, max_len=None):
        self.max_len = check_max_len(max_len)
        self.current = 0
        self.bars = np.zeros((max_len, 9), dtype=np.float32)
        self.timestamps = np.zeros((max_len), dtype=np.float32)

    def append_with_date_time(self, bar, datetime):
        """
            TODO:Convert datetime to timestamp
        """

        if self.current == self.max_len:
            new_bars = np.zeros((self.max_len*2, 9))
            new_timestamps = np.zeros((self.max_len*2))

            new_bars[0:self.max_len] = self.bars
            new_timestamps[0:self.max_len] = self.new_timestamps

            self.max_len = self.max_len * 2

        self.bars[self.current] = bar
        self.timestamps[self.current] = datetime.timestamp()
        self.current += 1
 

        
    """
        Convert To Single Price series
    """