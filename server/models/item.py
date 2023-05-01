from mongoengine import Document
from mongoengine.fields import *

class Item(Document):
    name = StringField(primary_key=True)
    description = StringField()
    placement = StringField()
    