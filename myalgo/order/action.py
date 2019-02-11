from enum import Enum, unique


@unique
class Action(Enum):
    BUY = 1
    BUY_TO_COVER = 2
    SELL = 3
    SELL_SHORT = 4
