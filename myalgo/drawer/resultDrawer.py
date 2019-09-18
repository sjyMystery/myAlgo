import matplotlib.pyplot as plt
import numpy as np

from myalgo.logger import get_logger
from myalgo.optimizer.results import ResultModel


class ResultDrawer:
    logger = get_logger('Drawer Logger')

    def __init__(self, results: [ResultModel], dpi: int = 128):
        self.__results = results
        self.__dpi = dpi

    def __draw_contour(self, ax2, low_bound=None, upper_bound=None, param_name="sharp_ratio"):
        def judge(v):

            rtv = True

            if low_bound is not None:
                rtv = rtv and low_bound <= v

            if upper_bound is not None:
                rtv = rtv and v <= upper_bound

            return rtv

        new_line = [np.array([line.p1, line.p2, getattr(line, param_name)]) for line in self.__results if
                    judge(line.sharp_ratio)]

        if len(new_line) <= 4:
            self.logger.debug('NO RESULTS SELECTED')
            return

        new_line = np.array(new_line)

        points = new_line[:, 0:2]

        x = points[:, 0]
        y = points[:, 1]
        z = new_line[:, 2]

        ax2.tricontour(x, y, z, levels=14, linewidths=0.5, colors='k')
        cntr2 = ax2.tricontourf(x, y, z, levels=14, cmap="coolwarm")
        ax2.plot(x, y, 'ko', ms=0.1)
        ax2.set_title(f'(p1,p2) and {param_name}')
        ax2.locator_params(nbins=40)
        ax2.grid()

        return cntr2
        # p.subplots_adjust(hspace=0.5)

    def draw_contour(self, save_path, low_bound=None, upper_bound=None, param_name=None):
        fig = plt.figure(dpi=self.__dpi)
        ax = fig.subplots(nrows=1)
        cntr2 = self.__draw_contour(ax, low_bound, upper_bound, param_name)
        if cntr2 is None:
            return
        fig.colorbar(cntr2, ax=ax)
        fig.savefig(save_path)

    def __draw_line(self, ax, low_bound=None, upper_bound=None, param_name="sharp_ratio"):
        def judge(v):
            rtv = True
            if low_bound is not None:
                rtv = rtv and low_bound <= v

            if upper_bound is not None:
                rtv = rtv and v <= upper_bound

            return rtv

        new_line = [np.array([line.p1, getattr(line, param_name)]) for line in self.__results if
                    judge(line.sharp_ratio)]
        new_line = np.array(new_line)
        if len(new_line) is 0:
            self.logger.error('NO RESULTS SELECTED')
            return

        pair = new_line
        pair = pair[np.argsort(pair[:, 0])]
        ax.plot(pair[:, 0], pair[:, 1])
        ax.set(xlabel='p1', ylabel=param_name,
               title=f'p1-{param_name} curve')
        ax.grid()

    def draw_line(self, save_path, low_bound=None, upper_bound=None, param_name="sharp_ratio"):
        fig = plt.figure(dpi=self.__dpi)
        ax = fig.subplots(nrows=1)
        self.__draw_line(ax, low_bound, upper_bound, param_name)
        fig.savefig(save_path)

    def draw_lines(self, save_path,
                   params=["sharp_ratio", "ret", "win_rate", "trade_count", "draw_down", "plr", "draw_down_duration"]):
        fig = plt.figure(dpi=self.__dpi)

        n = len(params)

        fig.set_figheight(n * 3)
        fig.set_figwidth(12)

        axex = fig.subplots(ncols=1, nrows=len(params))
        i = 0
        for param in params:
            ax = axex[i] if n > 1 else axex
            self.__draw_line(ax, param_name=param)
            i += 1

        fig.subplots_adjust(wspace=0.5, hspace=0.5)

        fig.savefig(save_path)

    def draw_contours(self, save_path,
                      params=["sharp_ratio", "ret", "win_rate", "trade_count", "draw_down", "plr",
                              "draw_down_duration"]):

        n = len(params)

        fig = plt.figure(dpi=self.__dpi, figsize=(25, n * 25))
        axex = fig.subplots(ncols=1, nrows=len(params))
        i = 0
        for param in params:
            ax = axex[i] if n > 1 else axex
            cntr2 = self.__draw_contour(ax, param_name=param)
            i += 1
            if cntr2 is not None:
                fig.colorbar(cntr2, ax=ax)

        fig.subplots_adjust(wspace=0.5, hspace=0.5)

        fig.savefig(save_path)
