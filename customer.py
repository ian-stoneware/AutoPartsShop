from flask import jsonify
from user import User
from datetime import datetime
from db import db
from wechatpy.pay import WeChatPay
from alipay import AliPay
import stripe

class Customer:
    def __init__(self, user: User):
        if user.role != 'customer':
            raise ValueError("User is not a customer")
        self.user = user

    def make_order(self, productIdList):
        from order import Order, order_product
        from product import Product
        total = 0.0
        products = []

        for productId in productIdList:
            product = Product.query.get(productId)
            if product and product.stock > 0:
                total += product.price
                product.stock -= 1
                products.append(product)
            else:
                print(f"Product {productId} is out of stock or doesn't exist.")
                return

        new_order = Order(
            userId=self.user.userId,
            totalPrice=total,
            payMethod='unpaid',
            date=datetime.utcnow(),
            status='pending'
        )

        new_order.productList.extend(products)
        db.session.add(new_order)

        db.session.commit()
        print(f"Order {new_order.orderId} created for customer {self.user.name}.")
        return new_order


    def make_payment(self, order_id, payment_method):
        from order import Order

        if payment_method not in ['alipay', 'wechat', 'credit_card']:
            raise Exception("Unsupported payment method")

        order = Order.query.get(order_id)
        if not order or order.userId != self.user.userId:
            raise Exception("Order not found or access denied")

        if payment_method == 'wechat':
            return 'success'
        elif payment_method == 'alipay':
            return 'success'
        elif payment_method == 'credit_card':
            return 'success'
        else:
            return 'failure'


    def view_order(self, order_id):
        from order import Order
        order = Order.query.filter_by(id=order_id, customerId=self.user.userId).first()
        if order:
            print(f"Order ID: {order.id}, Total: ${order.totalPrice:.2f}, Status: {order.status}, Date: {order.date}")
        else:
            print("Order not found.")

    def cancel_order(self, order_id):
        from order import Order
        order = Order.query.filter_by(orderId=order_id, userId=self.user.userId).first()
        if order and order.status not in ['cancelled', 'shipped']:
            order.status = "cancelled"
            db.session.commit()
            print(f"Order {order_id} cancelled.")
        else:
            print("Order cannot be cancelled.")

