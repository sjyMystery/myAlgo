import abc

import six

from myalgo.config import dispatchprio


@six.add_metaclass(abc.ABCMeta)
class Subject(object):

    def __init__(self):
        self.__dispatch_priority = dispatchprio.LAST

    # This may raise.
    @abc.abstractmethod
    def start(self):
        pass

    # This should not raise.
    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    # This should not raise.
    @abc.abstractmethod
    def join(self):
        raise NotImplementedError()

    # Return True if there are not more events to dispatch.
    @abc.abstractmethod
    def eof(self):
        raise NotImplementedError()

    # Dispatch events. If True is returned, it means that at least one event was dispatched.
    @abc.abstractmethod
    def dispatch(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def peek_datetime(self):
        # Return the datetime for the next event.
        # This is needed to properly synchronize non-realtime subjects.
        # Return None since this is a realtime subject.
        raise NotImplementedError()

    @property
    def dispatch_priority(self):
        return self.__dispatch_priority

    @dispatch_priority.setter
    def dispatch_priority(self, value):
        self.__dispatch_priority = value

    def on_dispatch_priority_registered(self, dispatcher):
        # Called when the subject is registered with a dispatcher.
        pass