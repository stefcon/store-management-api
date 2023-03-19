from flask_sqlalchemy import SQLAlchemy
import enum

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "product_category"

    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)


class Product(database.Model):
    __tablename__ = "products"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    quantity = database.Column(database.Integer, nullable=False)
    price = database.Column(database.Float, nullable=False)

    categories = database.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")
    requests = database.relationship("Request", back_populates="product")

    def __repr__(self):
        return f"{self.id},{self.name},{self.quantity},{self.price},{self.categories}"


class Category(database.Model):
    __tablename__ = "categories"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")

    def __repr__(self):
        return self.name


class Request(database.Model):
    __tablename__ = "requests"

    id = database.Column(database.Integer, primary_key=True)
    price = database.Column(database.Float, nullable=False)
    requested = database.Column(database.Integer, nullable=False)
    received = database.Column(database.Integer, nullable=False)

    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    product = database.relationship("Product", back_populates="requests")
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)
    order = database.relationship("Order", back_populates="requests")


class OrderStatus(enum.Enum):
    completed = "COMPLETE"
    pending = "PENDING"


class Order(database.Model):
    __tablename__ = "orders"

    id = database.Column(database.Integer, primary_key=True)
    total_price = database.Column(database.Float, nullable=False)
    finished_requests = database.Column(database.Integer, nullable=False, default=0)
    status = database.Column(database.Enum(OrderStatus), nullable=False)
    timestamp = database.Column(database.DateTime, nullable=False)

    user_mail = database.Column(database.String(256), nullable=False)
    requests = database.relationship("Request", back_populates="order")



