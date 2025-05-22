from user import User
from product import Product
from order import Order
from db import db

class OperatingSpecialist(User):
	def __init__(self, user: User):
		if user.role != 'operating specialist':
			raise ValueError("User is not an Operating Specialist")
		self.user = user

	def add_product(self, **kwargs):
		product = Product(**kwargs)
		db.session.add(product)
		db.session.commit()
		print(f"Product '{product.productName}' added successfully.")

	def delete_product(self, productId):
		product = Product.query.get(productId)
		if product:
			db.session.delete(product)
			db.session.commit()
			print(f"Product ID {productId} deleted successfully.")
		else:
			print("Product not found.")

	def update_product(self, productId, **kwargs):
		product = Product.query.get(productId)
		if not product:
			print("Product not found.")
			return
		for key, value in kwargs.items():
			if hasattr(product, key):
				setattr(product, key, value)
		db.session.commit()
		print(f"Product ID {productId} updated successfully.")

	def process_order(self, orderId):
		order = Order.query.get(orderId)
		if not order:
			print("Order not found.")
			return
		if order.status != 'processed':
			order.status = 'processed'
			db.session.commit()
			print(f"Order ID {orderId} marked as processed.")
		else:
			print(f"Order ID {orderId} is already processed.")

