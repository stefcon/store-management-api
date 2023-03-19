import json
from flask import Flask
from redis import Redis
from products.configuration import Configuration
from products.models import *
from sqlalchemy import and_
from flask_jwt_extended import JWTManager

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def get_or_insert_category(category_name):
    category = Category.query.filter(Category.name == category_name).first()
    if not category:
        # If category doesn't exist, create its instance
        category = Category(name=category_name)
        database.session.add(category)
        database.session.commit()
    return category


def insert_product(data):
    product = Product(name=data["name"], quantity=int(data["quantity"]), price=float(data["price"]))
    database.session.add(product)
    database.session.commit()

    for category_name in data["categories"]:
        database.session.refresh(product)

        # Getting or inserting category instance
        category = get_or_insert_category(category_name)

        # Link product with its category
        product_category = ProductCategory(productId=product.id, categoryId=category.id)
        database.session.add(product_category)
        database.session.commit()
    return product


def update_product(product, data):
    current_quantity = product.quantity
    current_price = product.price
    delivery_quantity = int(data["quantity"])
    delivery_price = float(data["price"])

    product.price = (current_quantity * current_price + delivery_quantity * delivery_price) / \
                    (current_quantity + delivery_quantity)
    product.quantity += delivery_quantity
    database.session.add(product)
    database.session.commit()


def update_pending_orders(product):
    # Fetching all pending orders, sorted ascending by their id
    orders = Order.query.filter(Order.status == OrderStatus.pending).order_by(Order.timestamp).all()
    if not orders:
        return

    for order in orders:
        # Fetching all requests that aren't finished and requested given product
        order_requests = Request.query.join(Order)\
            .filter(and_(Request.requested != Request.received, Request.productId == product.id,
                         Request.orderId == order.id)).all()
        if not order_requests:
            continue

        for r in order_requests:
            # Update request and product accordingly, until the product all requests run out
            needed_quantity = r.requested - r.received
            available_quantity = min(product.quantity, needed_quantity)

            r.received += available_quantity
            database.session.add(r)
            database.session.commit()

            product.quantity -= available_quantity
            database.session.add(product)
            database.session.commit()

            if r.received == r.requested:
                order.finished_requests += 1
            if product.quantity == 0:
                break
        # If all order's requests are fulfilled, change its status
        if order.finished_requests == len(order.requests):
            order.status = OrderStatus.completed
        database.session.add(order)
        database.session.commit()

        # We are finished if the product runs out
        if product.quantity == 0:
            break


def main():
    database.init_app(application)
    while True:
        with Redis(host=Configuration.REDIS_HOST) as redis:
            data = json.loads(redis.blpop(Configuration.REDIS_PRODUCTS_LIST, 0)[1])
            print(data)
        with application.app_context() as context:
            # Fetching product (if it exists)
            product = Product.query.filter(Product.name == data["name"]).first()
            if not product:
                # Create new product and insert it into database
                insert_product(data)

                # Impossible to have pending orders for product which didn't exist until now, continue
                continue
            database.session.add(product)
            # Product already exists in the database, check if categories match and if it does, update it
            if sorted(data["categories"]) == sorted([str(cat) for cat in product.categories]):
                update_product(product, data)
                update_pending_orders(product)
            else:
                print("Categories do not match!")


if __name__ == "__main__":
    main()
