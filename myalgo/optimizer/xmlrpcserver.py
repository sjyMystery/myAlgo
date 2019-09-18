import threading
import time

from six.moves import xmlrpc_server

import myalgo.logger
from myalgo.optimizer import base
from myalgo.optimizer import results
from myalgo.optimizer import serialization

logger = myalgo.logger.get_logger(__name__)


class AutoStopThread(threading.Thread):
    def __init__(self, server):
        super(AutoStopThread, self).__init__()
        self.__server = server

    def run(self):
        while self.__server.jobsPending():
            time.sleep(1)
        self.__server.stop()


class Job(object):
    def __init__(self, strategyParameters):
        self.__strategyParameters = strategyParameters
        self.__bestResult = None
        self.__bestParameters = None
        self.__id = id(self)

    def getId(self):
        return self.__id

    def getNextParameters(self):
        ret = None
        if len(self.__strategyParameters):
            ret = self.__strategyParameters.pop()
        return ret


# Restrict to a particular path.
class RequestHandler(xmlrpc_server.SimpleXMLRPCRequestHandler):
    rpc_paths = ('/myalgoRPC',)


class Server(xmlrpc_server.SimpleXMLRPCServer):
    def __init__(self, strategy_name, paramSource, resultSinc, barFeed, address, port, autoStop=True, batchSize=200,
                 result_file="result.sqlite"):
        assert batchSize > 0, "Invalid batch size"

        xmlrpc_server.SimpleXMLRPCServer.__init__(
            self, (address, port), requestHandler=RequestHandler, logRequests=False, allow_none=True
        )
        # super(Server, self).__init__(
        # (address, port), requestHandler=RequestHandler, logRequests=False, allow_none=True
        # )

        self.__batchSize = batchSize
        self.__paramSource = paramSource
        self.__resultSinc = resultSinc
        self.__barFeed = barFeed
        self.__instrumentsAndBars = None  # Serialized instruments and bars for faster retrieval.
        self.__barsFreq = None
        self.__activeJobs = {}
        self.__lock = threading.Lock()
        self.__startedServingEvent = threading.Event()
        self.__forcedStop = False
        self.__bestResult = None
        self.__resultSaver = results.ResultManager(strategy_name=strategy_name, file_name=result_file)
        if autoStop:
            self.__autoStopThread = AutoStopThread(self)
        else:
            self.__autoStopThread = None

        self.register_introspection_functions()
        self.register_function(self.getInstrumentsAndBars, 'getInstrumentsAndBars')
        self.register_function(self.getBarsFrequency, 'getBarsFrequency')
        self.register_function(self.getNextJob, 'getNextJob')
        self.register_function(self.pushJobResults, 'pushJobResults')
        self.register_function(self.jobFinished, 'jobFinished')
    def getInstrumentsAndBars(self):

        return self.__instrumentsAndBars

    def getBarsFrequency(self):
        return self.__barsFreq

    def getNextJob(self):
        ret = None

        with self.__lock:
            # Get the next set of parameters.
            params = [p.args for p in self.__paramSource.getNext(self.__batchSize)]

            # Map the active job
            if len(params):
                ret = Job(params)
                self.__activeJobs[ret.getId()] = ret

        return serialization.dumps(ret)

    def jobsPending(self):
        if self.__forcedStop:
            return False

        with self.__lock:
            jobsPending = not self.__paramSource.eof()
            activeJobs = len(self.__activeJobs) > 0

        return jobsPending or activeJobs

    def jobFinished(self, jobId):
        jobId = serialization.loads(jobId)
        with self.__lock:
            try:
                del self.__activeJobs[jobId]
            except KeyError:
                return

    def pushJobResults(self, result, parameters, workerName):
        result = serialization.loads(result)
        parameters = serialization.loads(parameters)
        p = base.Parameters(*parameters)
        if result is not None:
            self.__resultSaver.save(p1=parameters[0], p2=parameters[1], win_rate=result["win_rate"],
                                    profit_rate=result["profit_rate"], ret=result["ret"], draw_down=result["dd"],
                                    draw_down_duration=result["ddd"],
                                    trade_count=result["trade_count"], sharp_ratio=result["sharp"], plr=result["plr"]
                                    )

    def waitServing(self, timeout=None):
        return self.__startedServingEvent.wait(timeout)

    def stop(self):
        self.shutdown()

    def serve(self):
        try:
            # Initialize instruments, bars and parameters.
            logger.info("Loading bars")
            loadedBars = []
            for dateTime, bars in self.__barFeed:
                loadedBars.append(bars)
            instruments = self.__barFeed.registered_instruments
            self.__instrumentsAndBars = serialization.dumps((instruments, loadedBars))
            self.__barsFreq = self.__barFeed.frequency.value

            if self.__autoStopThread:
                self.__autoStopThread.start()

            logger.info("Started serving")
            self.__startedServingEvent.set()
            self.serve_forever()
            logger.info("Finished serving")

            if self.__autoStopThread:
                self.__autoStopThread.join()
        except Exception as e:
            logger.error(f'run exception,{e}')
        finally:
            self.__forcedStop = True
