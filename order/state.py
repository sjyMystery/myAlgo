from enum import unique, Enum


@unique
class State(Enum):
    INITIAL = 1
    SUBMITTED = 2
    ACCEPTED = 3
    CANCELED = 4
    PARTIALLY_FILLED = 5
    FILLED = 6
