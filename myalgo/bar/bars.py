import six


class Bars(object):
    """A group of :class:`Bar` objects.

    :param barDict: A map of instrument to :class:`Bar` objects.
    :type barDict: map.

    .. note::
        All bars must have the same datetime.
    """

    def __init__(self, bar_dict):
        if len(bar_dict) == 0:
            raise Exception("No bars supplied")

        # Check that bar datetimes are in sync
        first_date_time = None
        first_instrument = None
        for instrument, currentBar in six.iteritems(bar_dict):
            if first_date_time is None:
                first_date_time = currentBar.start_date
                first_instrument = instrument
            elif currentBar.start_date != first_date_time:
                raise Exception("Bar data times are not in sync. %s %s != %s %s" % (
                    instrument,
                    currentBar.start_date,
                    first_instrument,
                    first_date_time
                ))

        self.__barDict = bar_dict
        self.__dateTime = first_date_time

    def __getitem__(self, instrument):
        return self.__barDict[instrument]

    def __contains__(self, instrument):
        return instrument in self.__barDict

    @property
    def items(self):
        return list(self.__barDict.items())

    @property
    def keys(self):
        return list(self.__barDict.keys())

    @property
    def instruments(self):
        """Returns the instrument symbols."""
        return list(self.__barDict.keys())

    @property
    def datetime(self):
        """Returns the :class:`datetime.datetime` for this set of bars."""
        return self.__dateTime

    def bar(self, instrument):
        return self.__barDict.get(instrument, None)
