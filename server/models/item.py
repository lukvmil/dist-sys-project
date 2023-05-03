from mongoengine import Document
from mongoengine.fields import *

class Item(Document):
    name = StringField(primary_key=True)
    tag = StringField()
    description = StringField()
    placement = StringField()
    