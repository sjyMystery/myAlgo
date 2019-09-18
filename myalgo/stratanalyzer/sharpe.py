import math

from myalgo import stratanalyzer
from myalgo.stratanalyzer import returns
from myalgo.utils import stats


def days_traded(begin, end):
    delta = end - begin
    ret = delta.days + 1
    return ret


# :param returns: The returns.
# :param riskFreeRate: The risk free rate per annum.
# :param tradingPeriods: The number of trading periods per annum.
# :param annualized: True if the sharpe ratio should be annualized.
# * If using daily bars, tradingPeriods should be set to 252.
# * If using hourly bars (with 6.5 trading hours a day) then tradingPeriods should be set to 252 * 6.5 = 1638.
def sharpe_ratio(returns, riskFreeRate, tradingPeriods, annualized=True):
    ret = 0.0

    # From http://en.wikipedia.org/wiki/Sharpe_ratio: if Rf is a constant risk-free return throughout the period,
    # then stddev(R - Rf) = stddev(R).
    volatility = stats.stddev(returns, 1)

    if volatility != 0:
        rfPerReturn = riskFreeRate / float(tradingPeriods)
        avgExcessReturns = stats.mean(returns) - rfPerReturn
        ret = avgExcessReturns / volatility

        if annualized:
            ret = ret * math.sqrt(tradingPeriods)
    return ret


# :param returns: The returns.
# :param riskFreeRate: The risk free rate per annum.
# :param firstDateTime: The first datetime in the period.
# :param lastDateTime: The last datetime in the period.
# :param annualized: True if the sharpe ratio should be annualized.
def sharpe_ratio_2(returns, riskFreeRate, firstDateTime, lastDateTime, annualized=True):
    ret = 0.0

    # From http://en.wikipedia.org/wiki/Sharpe_ratio:
    # if Rf is a constant risk-free return throughout the period, then stddev(R - Rf) = stddev(R).
    volatility = stats.stddev(returns, 1)

    if volatility != 0:
        # We use 365 instead of 252 becuase we wan't the diff from 1/1/xxxx to 12/31/xxxx to be 1 year.
        yearsTraded = days_traded(firstDateTime, lastDateTime) / 365.0

        riskFreeRateForPeriod = riskFreeRate * yearsTraded
        rfPerReturn = riskFreeRateForPeriod / float(len(returns))

        avgExcessReturns = stats.mean(returns) - rfPerReturn
        ret = avgExcessReturns / volatility
        if annualized:
            ret = ret * math.sqrt(len(returns) / yearsTraded)
    return ret


class SharpeRatio(stratanalyzer.StrategyAnalyzer):
    """A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates
    Sharpe ratio for the whole portfolio.

    :param useDailyReturns: True if daily returns should be used instead of the returns for each bar.
    :type useDailyReturns: boolean.
    """

    def __init__(self, useDailyReturns=True):
        super(SharpeRatio, self).__init__()
        self.__useDailyReturns = useDailyReturns
        self.__returns = []

        # Only use when self.__useDailyReturns == False
        self.__firstDateTime = None
        self.__lastDateTime = None
        # Only use when self.__useDailyReturns == True
        self.__currentDate = None

    def getReturns(self):
        return self.__returns

    def beforeAttach(self):
        # Get or create a shared ReturnsAnalyzerBase
        analyzer = returns.ReturnsAnalyzerBase.getOrCreateShared(self.strat)
        analyzer.getEvent().subscribe(self.__onReturns)

    def __onReturns(self, dateTime, returnsAnalyzerBase):
        netReturn = returnsAnalyzerBase.getNetReturn()
        if self.__useDailyReturns:
            # Calculate daily returns.
            if dateTime.date() == self.__currentDate:
                self.__returns[-1] = (1 + self.__returns[-1]) * (1 + netReturn) - 1
            else:
                self.__currentDate = dateTime.date()
                self.__returns.append(netReturn)
        else:
            self.__returns.append(netReturn)
            if self.__firstDateTime is None:
                self.__firstDateTime = dateTime
            self.__lastDateTime = dateTime

    def getSharpeRatio(self, riskFreeRate, annualized=True):
        """
        Returns the Sharpe ratio for the strategy execution. If the volatility is 0, 0 is returned.

        :param riskFreeRate: The risk free rate per annum.
        :type riskFreeRate: int/float.
        :param annualized: True if the sharpe ratio should be annualized.
        :type annualized: boolean.
        """

        if not isinstance(annualized, bool):
            raise Exception("tradingPeriods parameter is not supported anymore.")

        if self.__useDailyReturns:
            ret = sharpe_ratio(self.__returns, riskFreeRate, 252, annualized)
        else:
            ret = sharpe_ratio_2(self.__returns, riskFreeRate, self.__firstDateTime, self.__lastDateTime, annualized)
        return ret
