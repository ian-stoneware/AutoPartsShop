from datetime import datetime
from customer import Customer
from order import Order

class Receipt:

    def __init__(self, order: Order):
        self._date: datetime = order.date
        self._receiptId: int = order.orderId  # Use orderId as receiptId
        self._customer = order.customer  # Full customer object
        self._totalPrice: float = order.totalPrice
        self._payMethod: str = order.payMethod
        self._order: Order = order

    def saveAsPic(self, filepath):

        print(f"Saving receipt {self._receiptId} as image to {filepath}...")
        pass

    def __str__(self):
        return (f"Receipt ID: {self._receiptId}\n"
                f"Date: {self._date}\n"
                f"Customer: {self._customer.name}\n"
                f"Total: ${self._totalPrice:.2f}\n"
                f"Payment Method: {self._payMethod}\n"
                f"Order ID: {self._order.orderId}")

