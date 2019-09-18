import matplotlib.pyplot as plt

from myalgo.stratanalyzer.indicators import Indicators


class IndicatorPlot:
    def __init__(self, analyzer: Indicators):
        self.__analyzer = analyzer
        self.__fig = plt.figure(f'{analyzer.strategy.name} on {analyzer.instrument}')

    def draw_all(self, save_path):
        intergals = self.__analyzer.all_int

        n = len(intergals)

        self.__fig.set_figheight(n * 10)
        self.__fig.set_fighwidth(30)

        axex = self.__fig.subplots(ncols=1, nrows=len(intergals))
        i = 0
        for key, value in intergals.items():
            if (len(value) == 0):
                continue
            ax = axex[i] if len(intergals) > 1 else axex

            # x = value[:, 0]
            # y = value[:, 1]

            ax.plot(value[:, 0], value[:, 1])
            # ax.fill_between(x, y, 0, where=y > 0, facecolor='blue', interpolate=True)
            # ax.fill_between(x, y, 0, where=y < 0, facecolor='red', interpolate=True)
            ax.set(xlabel=key, ylabel='returns',
                   title=key)
            ax.grid()
            ax.locator_params(nbins=40)
            i += 1

        self.__fig.subplots_adjust(wspace=0.5, hspace=0.5)

        self.__fig.savefig(save_path)

    def draw_single(self, name):
        integral = self.__analyzer.integral(name)
        ax = self.__fig.subplots(ncols=1, nrows=1)
        ax.plot(integral[:, 0], integral[:, 1])
        ax.set(xlabel=name, ylabel='returns',
               title=f"{name} cum returns")
        ax.grid()
        self.__fig.subplots_adjust(wspace=0.5, hspace=0.5)
        return ax

    @property
    def figure(self):
        return self.__fig
