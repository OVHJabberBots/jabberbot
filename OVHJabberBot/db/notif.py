from OVHJabberBot.db.updatable_document import UpdatableDocument

from mongoengine import *

"""
upgrades
"""

def upgrade_add_times_field(values):
    if 'times' not in values or values['times'] is None:
        values['times'] = 3
    return values


class Notif(UpdatableDocument):
    meta = {'collection': 'notif'}
    name = StringField(required=True)
    times = IntField(default=3)

    schema_updates = {
        1: upgrade_add_times_field
    }

    def __repr__(self):
        return "<Notif name={} times={}>".format(self.name, self.times)

    def __str__(self):
        return "{} prevenu {} fois".format(self.name, self.times)
