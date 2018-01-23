from mongoengine import *

class Notif(Document):
    name = StringField(required=True)
