import numpy as np
from numba import njit,jitclass, float32, int32

DEFAULT_MAX_LEN = 30000000


def check_max_len(len):
    if len is None or len <= 0:
        return DEFAULT_MAX_LEN
    else:
        return len


price_serices_class = [
    ("max_len", int32)
    ("current", int32)
    ("price", float32[:])
]


@jitclass
class PriceSeries:
    def __init__(self, prices=None,current=None,max_len=None):

        self.max_len = check_max_len(max_len)

        if prices is not None and current is not None:
                self.prices = prices
                self.current = current
        else:
            self.current = 0
            self.prices = np.zeros((max_len), dtype=np.float32)

    def __getitem__(self, key):
        return self.prices[key]

    def reset(self, max_len=None):
        self.max_len = check_max_len(max_len)
        self.current = 0

        self.prices = np.zeros((max_len), dtype=np.float32)

    def append(self, value):

        if self.current < self.max_len:
            self.prices[self.current]
            self.current += 1
        else:
            new_block = np.zeros((self.max_len*2))
            new_block[0:self.max_len] = self.prices
            self.prices = new_block
            self.max_len = self.max_len * 2
