from flask_sqlalchemy import SQLAlchemy
import enum
database = SQLAlchemy()


class UserRole(enum.Enum):
    admin = "admin"
    storekeeper = "storekeeper"
    customer = "customer"


class User(database.Model):
    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key=True)
    email = database.Column(database.String(256), nullable=False, unique=True)
    password = database.Column(database.String(256), nullable=False)
    forename = database.Column(database.String(256), nullable=False)
    surname = database.Column(database.String(256), nullable=False)

    roles = database.Column(database.Enum(UserRole), nullable=False)
    # roles = database.Column(database.String(256), nullable=False)
    # roles = database.relationship("Role", secondary=UserRole.__table__, back_populates="users")

    def __repr__(self):
        return f"{self.id},{self.email},{self.forename},{self.surname},{str(self.roles)}"
