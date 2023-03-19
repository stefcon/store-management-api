from datetime import timedelta
import os


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:123@{os.environ['DATABASE_URL']}/products_database"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    REDIS_HOST = os.getenv('REDIS_HOST', default="")
    REDIS_PRODUCTS_LIST = "products"
    JWT_DECODE_LEEWAY = 1
