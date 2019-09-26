from datetime import datetime


class Execution:
    def __init__(self, price: float, quantity: float, commission: float, datetime: datetime):
        self.price = price
        self.quantity = quantity
        self.commission = commission
        self.datetime = datetime

    def __str__(self):
        return "%s - Price: %s - Amount: %s - Fee: %s" % (
            self.datetime, self.price, self.quantity, self.commission)
