from db import db
from datetime import datetime
from customer import Customer
from product import Product


# Association table for many-to-many Order <-> Product relationship
order_product = db.Table(
    'order_product',
    db.Column('orderId', db.Integer, db.ForeignKey('Order.orderId'), primary_key=True),
    db.Column('productId', db.Integer, db.ForeignKey('Product.productId'), primary_key=True)
)

class Order(db.Model):
    __tablename__ = 'Order'

    orderId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('User.userId'), nullable=False)
    totalPrice = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payMethod = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')

    productList = db.relationship("Product", secondary=order_product, backref="orders")

    def __repr__(self):
        return f'<Order {self.orderId} - Customer {self.userId}>'
