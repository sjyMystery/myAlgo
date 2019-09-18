import numpy as np

from myalgo import stratanalyzer
from myalgo.logger import get_logger
from myalgo.strategy.position import Position

"""
想法：
对于每个需要被操作的Indicator，我们把它传入到这里，然后再将它attach上去。
每笔交易之前我们都可以记录Indicator的数值，然后记录下来。

然后当交易结束后，则得到一个交易与其之前的Indicator的一一对应

当然，有四个时间点，分别是：

入场前、入场后、出场前、出场后

每个时间点都对应有一堆indicator的数值

"""

logger = get_logger('indicator_analyz')


class Indicators(stratanalyzer.StrategyAnalyzer):
    """
        indicators:
            你所打算处理的Indicator的一个字典.
            注意需要传入一个Generator，而不是实例，因为Indicator将会在attach之前被给上priceDS

        instrument:
            标的
            这里用来分析具体针对某种策略的indicator
    """

    def __init__(self, indicators: dict, instrument):
        super(Indicators, self).__init__()
        self.__priceDS = None
        self.__instrument = instrument
        self.__indicatorGenerators = indicators
        self.__indicators = {}
        self.__pos_tracker = None

        self.__position_map = {}

    def __on_enter_start(self, position: Position):
        indicator_values = {}

        for key, value in self.__indicators.items():
            if value is not None:
                indicator_values[key] = value[-1]

        self.__position_map[position] = indicator_values

    def __on_exit_ok(self, position):
        pass

    def beforeAttach(self):
        self.strat.exit_ok_event.subscribe(self.__on_exit_ok)
        self.strat.enter_start_event.subscribe(self.__on_enter_start)
        self.__priceDS = self.strat.feed[self.__instrument].price
        for key, generator in self.__indicatorGenerators.items():
            self.__indicators[key] = generator(self.__priceDS)

    """
        我们按照最小精度1%来叠加，作积分曲线
        一般来说，取所有数值的绝对值的上界，再以10为低取对数，便知精度
    """

    def __integral(self, values, x):
        value_dic = {}

        """
            建立一个反向的表
            如果是空的点的话，说明没有意义，我们把它除去。
        """
        for key, value in enumerate(values):
            if value is None or x[key] is None:
                continue
            if not value_dic.__contains__(value):
                value_dic[value] = 1 + x[key]
            else:
                value_dic[value] *= 1 + x[key]

        values = list(filter(lambda x: x is not None, values))
        # 我们先将数值从小到大做一个排序
        sorted = np.unique(np.sort(values))

        results = []
        for key, value in enumerate(sorted):
            cum_prod = value_dic[value]
            if key > 0:
                cum_prod *= results[key - 1][1]
            results.append([value, cum_prod])

        return np.asarray(results)

    def integral(self, indicator_name):

        indicator_value_per_position = []
        position_ret = []

        for position, indicator_values in self.__position_map.items():
            if position.exitFilled():
                indicator_value_per_position.append(indicator_values[indicator_name])

                position_ret.append(position.getReturn())

        return self.__integral(indicator_value_per_position, position_ret)

    @property
    def all_int(self):
        result_dic = {}
        for key in self.__indicators.keys():
            logger.debug(f'calculating {key}')
            result_dic[key] = self.integral(key)
        return result_dic

    @property
    def instrument(self):
        return self.__instrument
