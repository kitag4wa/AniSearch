import tortoise
from tortoise import fields, models

class Users(models.Model):
    id = fields.IntField(pk=True)
    uid = fields.BigIntField(unique=True)

    username = fields.CharField(max_length=100, null=True)
    registered_at = fields.DatetimeField(auto_now_add=True)
    last_active = fields.DatetimeField(auto_now=True)
    is_blocked = fields.BooleanField(default=False)