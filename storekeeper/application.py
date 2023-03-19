import io
import csv
import json
from flask import Flask, request, Response
from configuration import Configuration
from decorator import role_check
from flask_jwt_extended import JWTManager
from redis import Redis

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def error_message(msg: str, status: int = 400):
    json_message = {
        "message": msg
    }
    return Response(json.dumps(json_message), status=status)


def send_to_redis(reader):
    for i, row in enumerate(reader):
        categories = row[0].split("|")
        name, quantity, price = row[1:]
        with Redis(host=Configuration.REDIS_HOST) as redis:
            product = {
                "categories": categories,
                "name": name,
                "quantity": quantity,
                "price": price
            }
            redis.rpush(Configuration.REDIS_PRODUCTS_LIST, json.dumps(product))


@application.route("/update", methods=["POST"])
@role_check("storekeeper")
def update_products():
    file = request.files.get("file", None)
    if file is None:
        return error_message("Field file is missing.")
    content = file.stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    read_rows = []
    # Data format: category0|category1,name,quantity,price
    for i, row in enumerate(reader):
        if len(row) != 4:
            return error_message(f"Incorrect number of values on line {i}.")

        # Reading data
        quantity, price = row[2:]

        # Validity of quantity
        try:
            quantity = int(quantity)
            if quantity < 0:
                return error_message(f"Incorrect quantity on line {i}.")
        except ValueError:
            return error_message(f"Incorrect quantity on line {i}.")

        # Validity of price
        try:
            price = float(price)
            if price < 0:
                return error_message(f"Incorrect price on line {i}.")
        except ValueError:
            return error_message(f"Incorrect price on line {i}.")

        read_rows.append(row)

    send_to_redis(read_rows)

    return Response("", 200)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0")
