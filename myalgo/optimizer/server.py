import myalgo.logger
from myalgo.optimizer import base
from myalgo.optimizer import xmlrpcserver

logger = myalgo.logger.get_logger(__name__)


class Results(object):
    """The result_image of the strategy executions."""

    def __init__(self, parameters, result):
        self.__parameters = parameters
        self.__result = result

    def getParameters(self):
        """Returns a sequence of parameter values."""
        return self.__parameters

    def getResult(self):
        """Returns the result for a given set of parameters."""
        return self.__result


def serve(strategy_name, barFeed, strategyParameters, address, port, batchSize=200, result_file="result.sqlite"):
    """Executes a server that will provide bars and strategy parameters for workers to use.

    :param barFeed: The bar feed that each worker will use to backtest the strategy.
    :type barFeed: :class:`myalgo.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is a tuple that holds parameter values**.
    :param address: The address to listen for incoming worker connections.
    :type address: string.
    :param port: The port to listen for incoming worker connections.
    :type port: int.
    :param batchSize: The number of strategy executions that are delivered to each worker.
    :type batchSize: int.
    :rtype: A :class:`Results` instance with the best result_image found or None if no result_image were obtained.
    """

    paramSource = base.ParameterSource(strategyParameters)
    resultSinc = base.ResultSinc()
    s = xmlrpcserver.Server(strategy_name, paramSource, resultSinc, barFeed, address, port, batchSize=batchSize,
                            result_file=result_file)
    logger.info("Starting server")
    s.serve()
    logger.info("Server finished")

    ret = None
    # bestResult, bestParameters = resultSinc.getBest()
    # if bestResult is not None:
    #     logger.info("Best final result %s with parameters %s" % (bestResult, bestParameters.args))
    #     ret = Results(bestParameters.args, bestResult)
    # else:
    #     logger.error("No result_image. All jobs failed or no jobs were processed.")
    return ret
