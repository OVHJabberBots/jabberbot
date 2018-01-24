from mongoengine import *

class Insulte(Document):
    meta = {'collection': 'insultes'}
    text = StringField(required=True)
