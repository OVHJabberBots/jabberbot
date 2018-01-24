from mongoengine import *

class Order(Document):
    name = StringField(required=True)
