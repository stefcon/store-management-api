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


@application.route("/productStatistics", methods=["GET"])
@role_check("admin")
def product_statistics():
    # Fetch all products
    products = Product.query.all()
    product_stats = []
    for product in products:
        # Fetch all requests connected to the product
        requests = Request.query.join(Order).filter(Request.productId == product.id).all()
        if not requests:
            continue

        sold = 0
        waiting = 0
        # Calculate info
        for r in requests:
            sold += r.requested
            waiting += r.requested - r.received
        product_stats.append(
            {
                "name": product.name,
                "sold": sold,
                "waiting": waiting
            }
        )
    return jsonify(statistics=product_stats)


@application.route("/categoryStatistics", methods=["GET"])
@role_check("admin")
def categories_statistics():
    # Fetch all products
    categories = Category.query.all()
    categories_stats = []
    for category in categories:
        requests = Request.query.join(Product).join(ProductCategory).join(Category)\
            .filter(Category.id == category.id).all()
        sold = 0
        for r in requests:
            sold += r.requested
        categories_stats.append((category.name, sold))
    categories_stats.sort(key=lambda x: (-x[1], x[0]))
    categories_stats = [item[0] for item in categories_stats]
    return jsonify(statistics=categories_stats)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0")