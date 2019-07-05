import numpy


def mean(values):
    ret = None
    if len(values):
        ret = numpy.array(values).mean()
    return ret


def stddev(values, ddof=1):
    ret = None
    if len(values):
        ret = numpy.array(values).std(ddof=ddof)
    return ret
