class Event(object):
    def __init__(self):
        self.__handlers = []
        self.__deferred = []
        self.__emitting = 0

    def __subscribe_impl(self, handler):
        assert not self.__emitting
        if handler not in self.__handlers:
            self.__handlers.append(handler)

    def __unsubscribe_impl(self, handler):
        assert not self.__emitting
        self.__handlers.remove(handler)

    def __apply_changes(self):
        assert not self.__emitting
        for action, param in self.__deferred:
            action(param)
        self.__deferred = []

    def subscribe(self, handler):
        if self.__emitting:
            self.__deferred.append((self.__subscribe_impl, handler))
        elif handler not in self.__handlers:
            self.__subscribe_impl(handler)

    def unsubscribe(self, handler):
        if self.__emitting:
            self.__deferred.append((self.__unsubscribe_impl, handler))
        else:
            self.__unsubscribe_impl(handler)

    def emit(self, *args, **kwargs):
        try:
            self.__emitting += 1
            for handler in self.__handlers:
                handler(*args, **kwargs)
        finally:
            self.__emitting -= 1
            if not self.__emitting:
                self.__apply_changes()

