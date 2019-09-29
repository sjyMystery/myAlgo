from myalgo.dataseries import PriceSeries


class High:
    def __init__(self, period: int, series: PriceSeries):
        self.series: PriceSeries = series
        self.period: int = period
