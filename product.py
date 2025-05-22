from db import db

class Product(db.Model):
    __tablename__ = 'Product'

    productId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    productName = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))

    def __repr__(self):
        return f"<Product {self.brand} {self.model} {self.name}>"
