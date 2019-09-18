import threading

import six


class Parameters(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ParameterSource(object):
    """
    Source for backtesting parameters. This class is thread safe.
    """

    def __init__(self, params):
        self.__iter = iter(params)
        self.__lock = threading.Lock()

    def getNext(self, count):
        """
        Returns the next parameters to use in a backtest.
        If there are no more parameters to try then an empty list is returned.

        :param count: The max number of parameters to return.
        :type count: int
        :rtype: list of Parameters.
        """

        assert count > 0, "Invalid number of parameters"

        ret = []
        with self.__lock:
            if self.__iter is not None:
                try:
                    while count > 0:
                        params = six.next(self.__iter)
                        # Backward compatibility when parameters don't yield Parameters.
                        if not isinstance(params, Parameters):
                            params = Parameters(*params)
                        ret.append(params)
                        count -= 1
                except StopIteration:
                    self.__iter = None
        return ret

    def eof(self):
        with self.__lock:
            return self.__iter is None


class ResultSinc(object):
    """
    Sinc for backtest result_image. This class is thread safe.
    """

    def __init__(self):
        self.__lock = threading.Lock()
        self.__bestResult = None
        self.__bestParameters = None

    def push(self, result, parameters):
        """
        Push strategy result_image obtained by running the strategy with the given parameters.

        :param result: The result obtained by running the strategy with the given parameters.
        :type result: float
        :param parameters: The parameters that yield the given result.
        :type parameters: Parameters
        """
        with self.__lock:
            self.onNewResult(result, parameters)
            # if result is not None and (self.__bestResult is None or result > self.__bestResult):
            #     self.__bestResult = result
            #     self.__bestParameters = parameters
            #     self.onNewBestResult(result, parameters)

    def getBest(self):
        with self.__lock:
            ret = self.__bestResult, self.__bestParameters
        return ret

    def onNewResult(self, result, parameters):
        pass

    def onNewBestResult(self, result, parameters):
        pass
