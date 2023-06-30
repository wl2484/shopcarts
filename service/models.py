"""
Shopcarts Service Models

Designed to support queries of the following APIs:
    GET  /shopcarts
    POST /shopcarts
    GET  /shopcarts/{shopcart_id}
    PUT  /shopcarts/{shopcart_id}
    DELETE /shopcarts/{shopcart_id}

    GET  /shopcarts/{shopcart_id}/items
    POST /shopcarts{shopcart_id}/items
    GET  /shopcarts/{shopcart_id}/items/{item_id}
    PUT  /shopcarts/{shopcart_id}/items/{item_id}
    DELETE /shopcarts/{shopcart_id}/items/{item_id}
"""

import logging
from abc import abstractmethod

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


# Function to initialize the tables in DB
def init_db(app):
    """ Initialize the Shopcart and the Item tables through SQLAlchemy """
    Shopcart.init_db(app)
    Item.init_db(app)


class DataValidationError(Exception):
    """ Used for object deserialization data validation errors """


class ModelBase:
    """ The shared base for models """

    def __init__(self):
        self.id = None

    @abstractmethod
    def serialize(self) -> dict:
        """ Transform the self object into a dictionary """

    @abstractmethod
    def deserialize(self, data: dict) -> None:
        """ Transform the dictionary into object """

    @classmethod
    def init_db(cls, app):
        """ Initialize DB Table """
        logger.info(f"Start initializing the {cls.__name__} Table")
        cls.app = app
        db.init_app(app)  # init the Flask app for SQLAlchemy
        app.app_context().push()
        db.create_all()  # create SQLAlchemy table
        logger.info(f"Done initializing the {cls.__name__} Table")

    @classmethod
    def get_all(cls):
        """ Get all objects in DB table """
        logger.info(f"Get all {cls.__name__}s")
        return cls.query.all()

    def create(self):
        """ Create an object in DB table """
        logger.info("Create %s", self.__repr__)
        self.id = None  # pylint: disable=invalid-name
        db.session.add(self)
        db.session.commit()

    def update(self):
        """ Update an object in DB table """
        logger.info("Update %s", self.__repr__)
        db.session.commit()

    def delete(self):
        """ Delete an object in DB table """
        logger.info("Delete %s", self.__repr__)
        db.session.delete(self)
        db.session.commit()


class Shopcart(db.Model, ModelBase):
    """ The Shopcart Table """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)  # correspond to customer_id
    name = db.Column(db.String(63), nullable=False)  # correspond to customer_name
    items = db.relationship("Item", backref="shopcart", passive_deletes=True)

    def __repr__(self):
        return f"{type(self).__name__}({self.id}, {self.name})"

    def serialize(self) -> dict:
        """ Transform the self object into a shopcart dictionary """
        shopcart = {
            "id": self.id,
            "name": self.name,
            "items": list()
        }
        for item in self.items:
            shopcart["items"].append(item.serialize())
        return shopcart

    def deserialize(self, data: dict) -> None:
        """
        Transform data dictionary into a shopcart object

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.id = data["id"]
            self.name = data["name"]
            items_js = data["items"]
            for item_js in items_js:
                item = Item()
                item.deserialize(item_js)
                self.items.append(item)
        except KeyError as error:
            raise DataValidationError(
                f"Invalid {type(self).__name__}: missing {error.args[0]}"
            ) from error
        except TypeError as error:
            raise DataValidationError(
                f"Invalid {type(self).__name__}: failed to deserialize request body\nError message: {error}"
            ) from error

    @classmethod
    def get_by_id(cls, id):
        """ Get shopcart by primary key: id """
        logger.info(f"Get {cls.__name__} by id={id}")
        return cls.query.get(id)

    @classmethod
    def find_by_name(cls, name):
        """Find shopcart(s) by name

        Args:
            name (string): the name of the Shopcarts you want to match
        """
        logger.info(f"Get {cls.__name__} by name={name}")
        return cls.query.filter(cls.name == name)


class Item(db.Model, ModelBase):
    """ The Item Table """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    shopcart_id = db.Column(db.Integer, db.ForeignKey('shopcart.id', ondelete="CASCADE"), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"{type(self).__name__}({self.shopcart_id}, {self.id}, {self.name}, {self.quantity}, {self.price})"

    def serialize(self) -> dict:
        """ Transform the self object into an item dictionary """
        return {
            "id": self.id,
            "shopcart_id": self.shopcart_id,
            "name": self.name,
            "quantity": self.quantity,
            "price": self.price
        }

    def deserialize(self, data: dict) -> None:
        """
        Transform data dictionary into an item object

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.id = data["id"]
            self.shopcart_id = data["shopcart_id"]
            self.name = data["name"]
            self.quantity = data["quantity"]
            self.price = data["price"]
        except KeyError as error:
            raise DataValidationError(
                f"Invalid {type(self).__name__}: missing {error.args[0]}"
            ) from error
        except TypeError as error:
            raise DataValidationError(
                f"Invalid {type(self).__name__}: failed to deserialize request body\nError message: {error}"
            ) from error
