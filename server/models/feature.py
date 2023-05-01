from mongoengine import Document
from mongoengine.fields import *

class Feature(Document):
    name = StringField(primary_key=True)
    tag = StringField()
    description = StringField()
    action = DictField()