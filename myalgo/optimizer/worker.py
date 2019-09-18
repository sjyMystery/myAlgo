import multiprocessing
import socket

import retrying
from six.moves import xmlrpc_client

import myalgo.logger
from myalgo.feed import OptimizerBarFeed
from myalgo.optimizer import serialization

wait_exponential_multiplier = 500
wait_exponential_max = 10000
stop_max_delay = 10000


def any_exception(exception):
    return True


@retrying.retry(wait_exponential_multiplier=wait_exponential_multiplier, wait_exponential_max=wait_exponential_max,
                stop_max_delay=stop_max_delay, retry_on_exception=any_exception)
def retry_on_network_error(function, *args, **kwargs):
    result = function(*args, **kwargs)
    return result


class Worker(object):
    def __init__(self, address, port, workerName=None, barFeed=None):
        url = "http://%s:%s/myalgoRPC" % (address, port)

        self.__logger = myalgo.logger.get_logger(workerName)
        self.__server = xmlrpc_client.ServerProxy(url, allow_none=True)
        if workerName is None:
            self.__workerName = socket.gethostname()
        else:
            self.__workerName = workerName

        if barFeed is not None:
            self.__feed = OptimizerBarFeed(barFeed.frequency, barFeed.instruments, barFeed.bars, barFeed.max_len)
        else:
            self.__feed = None

    def getLogger(self):
        return self.__logger

    def getInstrumentsAndBars(self):
        ret = retry_on_network_error(self.__server.getInstrumentsAndBars)
        ret = serialization.loads(ret)
        return ret

    def getBarsFrequency(self):
        ret = retry_on_network_error(self.__server.getBarsFrequency)
        ret = int(ret)
        return ret

    def getNextJob(self):
        ret = retry_on_network_error(self.__server.getNextJob)
        ret = serialization.loads(ret)
        return ret

    def pushJobResults(self, result, parameters):
        result = serialization.dumps(result)
        parameters = serialization.dumps(parameters)
        workerName = serialization.dumps(self.__workerName)
        retry_on_network_error(self.__server.pushJobResults, result, parameters, workerName)

    def jobFinished(self, jobId):
        jobId = serialization.dumps(jobId)
        retry_on_network_error(self.__server.jobFinished, jobId)

    def __processJob(self, job):
        parameters = job.getNextParameters()
        while parameters is not None:
            # Wrap the bars into a feed.
            self.getLogger().info("Running strategy with parameters %s" % (str(parameters)))
            result = None
            try:
                result = self.runStrategy(self.__feed.clone(), *parameters)
            except Exception as e:
                self.getLogger().exception("Error running strategy with parameters %s: %s" % (str(parameters), e))

            self.getLogger().info(f"result:{result} params:{parameters}")
            self.pushJobResults(result, parameters)

            # Run with the next set of parameters.
            parameters = job.getNextParameters()

        self.jobFinished(job.getId())

    # Run the strategy and return the result.
    def runStrategy(self, feed, parameters):
        raise Exception("Not implemented")

    def run(self):
        try:
            self.getLogger().info("Started running")
            # Get the instruments and bars.
            if not self.__feed:
                instruments, bars = self.getInstrumentsAndBars()
                barsFreq = self.getBarsFrequency()
                self.__feed = OptimizerBarFeed(barsFreq, instruments, bars, self)

            # Process jobs
            job = self.getNextJob()
            while job is not None:
                self.__processJob(job)
                job = self.getNextJob()
            self.getLogger().info("Finished running")
        except Exception as e:
            self.getLogger().exception("Finished running with errors: %s" % (e))


def worker_process(strategyClass, address, port, workerName, barFeed):
    class MyWorker(Worker):
        def runStrategy(self, barFeed, *args, **kwargs):
            strat = strategyClass(barFeed, *args, **kwargs)
            strat.run()
            return strat.result

    # Create a worker and run it.
    w = MyWorker(address, port, workerName, barFeed)

    w.run()


def run(strategyClass, address, port, workerCount=None, workerName=None, barFeed=None):
    """Executes one or more worker processes that will run a strategy with the bars and parameters supplied by the server.

    :param strategyClass: The strategy class.
    :param address: The address of the server.
    :type address: string.
    :param port: The port where the server is listening for incoming connections.
    :type port: int.
    :param workerCount: The number of worker processes to run. If None then as many workers as CPUs are used.
    :type workerCount: int.
    :param workerName: A name for the worker. A name that identifies the worker. If None, the hostname is used.
    :type workerName: string.
    :param barFeed: shared bar feed. Not necessary,but you can provide to reduce memory cost.
    """

    assert (workerCount is None or workerCount > 0)
    if workerCount is None:
        workerCount = multiprocessing.cpu_count()

    workers = []
    # Build the worker processes.
    for i in range(workerCount):
        workers.append(
            multiprocessing.Process(target=worker_process, args=(strategyClass, address, port, workerName, barFeed)))

    # Start workers
    for process in workers:
        process.start()

    # Wait workers
    for process in workers:
        process.join()
