import math


# Helper class to calculate PnL and returns over a single instrument (not the whole portfolio).
class PositionTracker(object):
    def __init__(self, round_quantity):
        self.round_quantity = round_quantity
        self.reset()

    def reset(self):
        self.__pnl = 0.0
        self.__avgPrice = 0.0  # Volume weighted average price per share.
        self.__position = 0.0
        self.__commissions = 0.0
        self.__totalCommited = 0.0  # The total amount commited to this position.

    def getPosition(self):
        return self.__position

    def getAvgPrice(self):
        return self.__avgPrice

    def getCommissions(self):
        return self.__commissions

    def getPnL(self, price=None, includeCommissions=True):
        """
        Return the PnL that would result if closing the position a the given price.
        Note that this will be different if commissions are used when the trade is executed.
        """

        ret = self.__pnl
        if price:
            ret += (price - self.__avgPrice) * self.__position
        if includeCommissions:
            ret -= self.__commissions
        return ret

    def getReturn(self, price=None, includeCommissions=True):
        ret = 0
        pnl = self.getPnL(price=price, includeCommissions=includeCommissions)
        if self.__totalCommited != 0:
            ret = pnl / float(self.__totalCommited)
        return ret

    def __openNewPosition(self, quantity, price):
        self.__avgPrice = price
        self.__position = quantity
        self.__totalCommited = self.__avgPrice * abs(self.__position)

    def __extendCurrentPosition(self, quantity, price):
        newPosition = self.round_quantity(self.__position + quantity)
        self.__avgPrice = (self.__avgPrice * abs(self.__position) + price * abs(quantity)) / abs(float(newPosition))
        self.__position = newPosition
        self.__totalCommited = self.__avgPrice * abs(self.__position)

    def __reduceCurrentPosition(self, quantity, price):
        # Check that we're closing or reducing partially
        assert self.round_quantity(abs(self.__position) - abs(quantity)) >= 0
        pnl = (price - self.__avgPrice) * quantity * -1

        self.__pnl += pnl
        self.__position = self.round_quantity(self.__position + quantity)
        if self.__position == 0:
            self.__avgPrice = 0.0

    def update(self, quantity, price, commission):
        assert quantity != 0, "Invalid quantity"
        assert price > 0, "Invalid price"
        assert commission >= 0, "Invalid commission"

        if self.__position == 0:
            self.__openNewPosition(quantity, price)
        else:
            # Are we extending the current position or going in the opposite direction ?
            currPosDirection = math.copysign(1, self.__position)
            tradeDirection = math.copysign(1, quantity)

            if currPosDirection == tradeDirection:
                self.__extendCurrentPosition(quantity, price)
            else:
                # If we're going in the opposite direction we could be:
                # 1: Partially reducing the current position.
                # 2: Completely closing the current position.
                # 3: Completely closing the current position and opening a new one in the opposite direction.
                if abs(quantity) <= abs(self.__position):
                    self.__reduceCurrentPosition(quantity, price)
                else:
                    newPos = self.__position + quantity
                    self.__reduceCurrentPosition(self.__position * -1, price)
                    self.__openNewPosition(newPos, price)

        self.__commissions += commission

    def buy(self, quantity, price, commission=0.0):
        assert quantity > 0, "Invalid quantity"
        self.update(quantity, price, commission)

    def sell(self, quantity, price, commission=0.0):
        assert quantity > 0, "Invalid quantity"
        self.update(quantity * -1, price, commission)
