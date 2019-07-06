import pickle

import six
from six.moves import xmlrpc_client


def dumps(obj):
    return pickle.dumps(obj)


def loads(serialized):
    if six.PY3 and isinstance(serialized, xmlrpc_client.Binary):
        serialized = serialized.data
    return pickle.loads(serialized)
