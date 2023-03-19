from datetime import timedelta
import os


class Configuration:
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    REDIS_HOST = os.getenv('REDIS_HOST', default="")
    REDIS_PRODUCTS_LIST = "products"
    JWT_DECODE_LEEWAY = 1
