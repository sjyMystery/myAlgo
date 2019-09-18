import datetime

from myalgo.drawer import indicatorPlot
from myalgo.drawer import strategyplot
from myalgo.feed import SQLiteFeed
from myalgo.indicator import rsi, highlow, ma, macd, atr, mad, volatility
from myalgo.stratanalyzer import indicators
from strategies import orindary

with_indicator = True
instrument = 'EURCHF'
from_date = datetime.date(2015, 1, 1)
to_date = datetime.date(2019, 1, 1)
p1 = 0.31
p2 = 0.11


def igen(indicator, *args):
    def I(i):
        return indicator(i, *args)

    return I


def ATRMONTH(i):
    return atr.ATR(i, 24 * 60 * 30)


def ATRWEEK(i):
    return atr.ATR(i, 24 * 60 * 7)


def ATRDAY(i):
    return atr.ATR(i, 24 * 60)


def ATR12H(i):
    return atr.ATR(i, 12 * 60)


def ATR4H(i):
    return atr.ATR(i, 240)


def ATR1H(i):
    print(i)
    return atr.ATR(i, 60)


def MACDN(i):
    return macd.MACD(i, 12, 26, 9)


def MACDN1(i):
    return macd.MACD(i, 40, 240, 8)


def MACDN2(i):
    return macd.MACD(i, 30, 180, 9)


def range40(i):
    return highlow.Range(i, 40)


def range240(i):
    return highlow.Range(i, 240)


def RSI60(i):
    return rsi.RSI(i, 60)


def RSI240(i):
    return rsi.RSI(i, 240)


def RSI30(i):
    return rsi.RSI(i, 30)


def RSI20(i):
    return rsi.RSI(i, 20)


def RSI10(i):
    return rsi.RSI(i, 10)


def RSI5(i):
    return rsi.RSI(i, 5)


def SMA40(i):
    return ma.SMA(i, 40)


def SMA80(i):
    return ma.SMA(i, 80)


def SMA120(i):
    return ma.SMA(i, 120)


def SMA240(i):
    return ma.SMA(i, 240)


def SMA20(i):
    return ma.SMA(i, 20)


i = indicators.Indicators({
    "RSI 4H": RSI240,
    "RSI 12H": igen(rsi.RSI, 12 * 60),
    "RSIDAY": igen(rsi.RSI, 24 * 60),
    "RSI5DAY": igen(rsi.RSI, 5 * 24 * 60),
    "RSI10DAY": igen(rsi.RSI, 10 * 24 * 60),
    "RSI15DAY": igen(rsi.RSI, 15 * 24 * 60),
    "RSI30DAY": igen(rsi.RSI, 30 * 24 * 60),
    "RSI3M": igen(rsi.RSI, 3 * 30 * 24 * 60),
    # "BOLL 1H 2S": igen(bollinger.BollingerBands, 60, 2),
    # "BOLL 1H 4S": igen(bollinger.BollingerBands, 60, 4),
    # "boll 1H 8S": igen(bollinger.BollingerBands, 60, 8),
    # "BOLL 4H 2S": igen(bollinger.BollingerBands, 4*60, 2),
    # "BOLL 4H 4S": igen(bollinger.BollingerBands,  4*60, 4),
    # "boll 4H 8S": igen(bollinger.BollingerBands,  4*60, 8),
    # "BOLL 12H 2S": igen(bollinger.BollingerBands,  12*60, 2),
    # "BOLL 12H 4S": igen(bollinger.BollingerBands,  12*60, 4),
    # "boll 12H 8S": igen(bollinger.BollingerBands, 12*60, 8),
    # "BOLL 1D 2S": igen(bollinger.BollingerBands, 24*60, 2),
    # "BOLL 1D 4S": igen(bollinger.BollingerBands, 24*60, 4),
    # "boll 1D 8S": igen(bollinger.BollingerBands, 24*60, 8),
    "Range Ratio 3h": igen(highlow.Range, 3 * 60),
    "Range Ratio 6h": igen(highlow.Range, 6 * 60),
    "Range Ratio 12h": igen(highlow.Range, 12 * 60),
    "Range Ratio 1D": igen(highlow.Range, 24 * 60),
    "MACDNORMAL": MACDN,
    "MACDNORMAL1": MACDN1,
    "MACDNORMAL2": MACDN2,
    "MACD 10,60,8": igen(macd.MACD, 10, 60, 8),
    "MACD 10,60,16": igen(macd.MACD, 10, 60, 16),
    "MACD 1h,12h,16": igen(macd.MACD, 60, 240, 16),
    "MACD 3h,12h,1h": igen(macd.MACD, 180, 12 * 60, 60),
    "MACD 1h,1day,1h": igen(macd.MACD, 60, 60 * 24, 60),
    "MACD 3h,1day,1h": igen(macd.MACD, 180, 60 * 24, 60),
    "MACD 3h,5day,1h": igen(macd.MACD, 180, 60 * 24 * 5, 60),
    "MACD 3h,15day,1h": igen(macd.MACD, 180, 60 * 24 * 15, 60),
    "MACD 1h,12h,8": igen(macd.MACD, 60, 12 * 60, 8),
    "MACD 1h,1day,8": igen(macd.MACD, 60, 24 * 60, 8),
    "SMAD 3h ": igen(mad.SMAD, 3 * 60),
    "SMAD 6h ": igen(mad.SMAD, 6 * 60),
    "SMAD 12h ": igen(mad.SMAD, 12 * 60),
    "SMAD 1day ": igen(mad.SMAD, 24 * 60),
    "SMAD 5day ": igen(mad.SMAD, 5 * 24 * 60),
    "SMAD 15day ": igen(mad.SMAD, 15 * 24 * 60),
    "SMAD 1Month ": igen(mad.SMAD, 30 * 24 * 60),
    "SMADRange 3h ": igen(mad.SMADRange, 3 * 60),
    "SMADRange 6h ": igen(mad.SMADRange, 6 * 60),
    "SMADRange 12h ": igen(mad.SMADRange, 12 * 60),
    "SMADRange 1day ": igen(mad.SMADRange, 24 * 60),
    "SMADRange 5day ": igen(mad.SMADRange, 5 * 24 * 60),
    "SMADRange 15day ": igen(mad.SMADRange, 15 * 24 * 60),
    "SMADRange 1 Month ": igen(mad.SMADRange, 30 * 24 * 60),
    "Volatility 3h ": igen(volatility.Volatility, 3 * 60),
    "Volatility 6h ": igen(volatility.Volatility, 6 * 60),
    "Volatility 12h ": igen(volatility.Volatility, 12 * 60),
    "Volatility 1day ": igen(volatility.Volatility, 24 * 60),
    "Volatility 5day ": igen(volatility.Volatility, 5 * 24 * 60),
    "Volatility 15day ": igen(volatility.Volatility, 15 * 24 * 60),
    "Volatility 1 Month ": igen(volatility.Volatility, 30 * 24 * 60),

    # "Slope 30 min": igen(linear.Slope, 30),
    # "Slope 1h ": igen(linear.Slope, 60),
    # "Slope 3h ": igen(linear.Slope, 3 * 60),
    # "Slope 6h ": igen(linear.Slope, 6 * 60),
    # "Slope 12h ": igen(linear.Slope, 12 * 60),
    # "Slope 1day ": igen(linear.Slope, 24 * 60),
    # "Slope 5day ": igen(linear.Slope, 5 * 24 * 60),
    # "Slope 15day ": igen(linear.Slope, 15 * 24 * 60),
    # "Slope 1 Month ": igen(linear.Slope, 30 * 24 * 60),
    # "ATRHOUR": ATR1H,
    # "ATR4H": ATR4H,
    # "ATR12H": ATR12H,
    # "ATRDAY": ATRDAY,
    # "ATRMONTH": ATRMONTH,
    # "ATRWEEK": ATRWEEK,
}, instrument)

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = SQLiteFeed(instruments=[instrument], table_name='bins', file_name='sqlite')
    feed.load_data(from_date, to_date)
    s = orindary.OrindaryStr(feed, p1, p2, instrument)

    if with_indicator:
        s.attachAnalyzer(i)
    plotter = strategyplot.StrategyPlotter(s)
    plotter.getOrCreateSubplot("returns").addDataSeries("simple returns", s.analyzers["ret"].getReturns())
    plotter.getOrCreateSubplot("cum ret").addDataSeries("cum returns", s.analyzers["ret"].getCumulativeReturns())

    s.run()

    if with_indicator:
        iplot = indicatorPlot.IndicatorPlot(i)
        iplot.draw_all(f'./result_image/indicators-{instrument}.pdf')
    plotter.savePlot(f'./result_image/curve-{instrument}.png')
