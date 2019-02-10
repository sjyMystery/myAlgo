from enum import Enum, unique


@unique
class Type(Enum):
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
