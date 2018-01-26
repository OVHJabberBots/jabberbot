from mongoengine import *


class UpdatableDocument(Document):
    meta = {'abstract': True}

    schema_version = IntField(default=0)
    updated = False

    schema_updates = {}

    def __init__(self, *args, **kwargs):
        values = self.schema_update(kwargs)
        super(UpdatableDocument, self).__init__(*args, **values)
        if self.updated:
            self.save()


    def schema_update(self, values):
        version = values.get('schema_version', 0)
        next_version = version + 1

        while self.schema_updates.get(next_version):
            self.updated = True
            update = self.schema_updates[next_version]
            update(values)
            values['schema_version'] = next_version
            next_version += 1

        return values