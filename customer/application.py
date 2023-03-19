import json
from datetime import datetime
from flask import Flask, request, Response, jsonify
from products.configuration import Configuration
from products.models import *
from sqlalchemy import and_
from decorator import role_check
from flask_jwt_extended import JWTManager, get_jwt_identity

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def error_message(msg: str, status: int = 400):
    json_message = {
        "message": msg
    }
    return Response(json.dumps(json_message), status=status)


def check_id_missing_error(requests, order):
    for ind, r in enumerate(requests):
        identifier = r.get("id", None)
        if identifier is None:
            return False, ind
    return True, -1


def check_quantity_missing_error(requests, order):
    for ind, r in enumerate(requests):
        quantity = r.get("quantity", None)
        if quantity is None:
            return False, ind
    return True, -1


def check_id_validity(requests, order):
    for ind, r in enumerate(requests):
        identifier = r.get("id", None)
        try:
            identifier = int(identifier)
            if identifier < 0:
                return False, ind
        except ValueError:
            return False, ind
    return True, -1


def check_quantity_validity(requests, order):
    for ind, r in enumerate(requests):
        quantity = r.get("quantity", None)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, ind
        except ValueError:
            return False, ind
    return True, -1


def check_product_validity(requests, order):
    for ind, r in enumerate(requests):
        identifier = int(r.get("id"))
        product = Product.query.filter(Product.id == identifier).first()
        if not product:
            return False, ind
    return True, -1


def check_order_validity(requests, order):
    check, ind = check_id_missing_error(requests, order)
    if not check:
        database.session.delete(order)
        database.session.commit()
        return error_message(f"Product id is missing for request number {ind}.")

    check, ind = check_quantity_missing_error(requests, order)
    if not check:
        database.session.delete(order)
        database.session.commit()
        return error_message(f"Product quantity is missing for request number {ind}.")

    check, ind = check_id_validity(requests, order)
    if not check:
        database.session.delete(order)
        database.session.commit()
        return error_message(f"Invalid product id for request number {ind}.")

    check, ind = check_quantity_validity(requests, order)
    if not check:
        database.session.delete(order)
        database.session.commit()
        return error_message(f"Invalid product quantity for request number {ind}.")

    check, ind = check_product_validity(requests, order)
    if not check:
        database.session.delete(order)
        database.session.commit()
        return error_message(f"Invalid product for request number {ind}.")

    return None


@application.route("/search", methods=["GET"])
@role_check("customer")
def search_products():
    name = request.args.get("name", "")
    category = request.args.get("category", "")

    categories = Category.query.join(ProductCategory).join(Product).filter(
        and_(Product.name.like(f"%{name}%"), Category.name.like(f"%{category}%"))).all()

    products = Product.query.join(ProductCategory).join(Category).filter(
        and_(Product.name.like(f"%{name}%"), Category.name.like(f"%{category}%"))).all()

    result = {
        "categories": [str(cat) for cat in categories],
        "products": []
    }
    for product in products:
        result["products"].append({
            "categories": [str(cat) for cat in product.categories],
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity
        })

    return Response(json.dumps(result), 200)


@application.route("/order", methods=["POST"])
@role_check("customer")
def order_products():
    requests = request.json.get("requests", "ERROR")
    if requests == "ERROR":
        return error_message("Field requests is missing.")

    # Fetching the mail of the user making an order
    identity = get_jwt_identity()
    # Creating new order
    order = Order(total_price=0, finished_requests=0, status=OrderStatus.pending,
                  timestamp=datetime.now(), user_mail=identity)
    database.session.add(order)
    database.session.commit()
    request_objects = []

    # Check if all requests in order are valid
    message = check_order_validity(requests, order)
    if message is not None:
        return message

    for ind, r in enumerate(requests):
        # Fetching id and quantity, if they exist
        identifier = int(r.get("id"))
        quantity = float(r.get("quantity"))

        product = Product.query.filter(Product.id == identifier).first()

        if product.quantity >= quantity:
            # Request is finished
            product.quantity -= quantity
            req = Request(price=product.price, requested=quantity, received=quantity,
                          productId=product.id, orderId=order.id)
            order.finished_requests += 1
        else:
            # Request remains to be finished
            req = Request(price=product.price, requested=quantity, received=product.quantity,
                          productId=product.id, orderId=order.id)
            product.quantity = 0

        # Update products info in the database
        database.session.add(product)
        database.session.commit()
        # Update total_price and insert into request_objects list (for later inserting)
        order.total_price += product.price * quantity
        request_objects.append(req)
    if order.finished_requests == len(requests):
        order.status = OrderStatus.completed
    # Insert order into the database
    database.session.add(order)
    database.session.commit()
    # Insert every created request for the order
    for r in request_objects:
        database.session.add(r)
        database.session.commit()

    # Return order's id as a response
    response = {
        "id": order.id
    }
    return Response(json.dumps(response), 200)


@application.route("/status", methods=["GET"])
@role_check("customer")
def orders_overview():
    identity = get_jwt_identity()
    order_list = []

    # Fetch all the orders based on user's identity (email)
    orders = Order.query.filter(Order.user_mail == identity).all()
    if orders:
        for order in orders:
            # Fetch all requests for the given order
            requests = Request.query.join(Order).filter(Request.orderId == order.id).all()
            request_list = []
            for r in requests:
                # Fetch request's product
                product = Product.query.filter(Product.id == r.productId).first()
                # Fetch product's categories
                categories = Category.query.join(ProductCategory).join(Product).filter(Product.id == product.id).all()
                # Create request entry
                request_list.append(
                        {
                            'categories': [str(cat) for cat in categories],
                            'name': product.name,
                            'price': r.price,
                            'received': r.received,
                            'requested': r.requested
                        }
                )
            order_entry = {
                'products': request_list,
                'price': order.total_price,
                'status': order.status.value,
                'timestamp': order.timestamp.isoformat(timespec='seconds') + 'Z'
            }
            order_list.append(order_entry)

    return jsonify(orders=order_list)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0")
