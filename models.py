from tortoise import fields
from tortoise.models import Model

from enum import Enum


class FilterAction(str, Enum):
    SKIP = "SKIP"
    PAUSE = "PAUSE"
    REPLACE = "REPLACE"


class FilterScope(str, Enum):
    GLOBAL = "GLOBAL"
    RECIPIENT = "RECIPIENT"
    DONOR = "DONOR"


class Filter(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    is_regex = fields.BooleanField(default=False)
    pattern = fields.CharField(max_length=1000)
    replace_with = fields.CharField(max_length=1000, null=True)
    is_active = fields.BooleanField(default=True)
    action = fields.CharEnumField(FilterAction, default=FilterAction.REPLACE)
    scope = fields.CharEnumField(FilterScope, default=FilterScope.RECIPIENT)
    recipient_channel = fields.ForeignKeyField("models.RecipientChannel", related_name="filters", null=True)
    donor_channel = fields.ForeignKeyField("models.DonorChannel", related_name="filters", null=True)

    def apply(self, text: str) -> str:
        if self.action != FilterAction.REPLACE:
            raise Exception("Only REPLACE action is supported")

        if self.is_regex:
            import re

            return re.sub(self.pattern, self.replace_with, text)

        else:
            return text.replace(self.pattern, self.replace_with)

    class Meta:
        table = "filters"

    def __str__(self):
        return f"Filter [{self.id}] {self.name}: {'regex ' if self.is_regex else ''}{self.pattern[:20]} -> {self.replace_with[:20]}"

    def __repr__(self):
        return f"Filter [{self.id}]"


class RecipientChannel(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    channel_id = fields.CharField(max_length=100)
    is_active = fields.BooleanField(default=True)
    max_forwarding_per_day = fields.IntField(default=0)  # 0 - unlimited
    filters = fields.ReverseRelation["Filter"]
    donor_channels = fields.ReverseRelation["DonorChannel"]

    class Meta:
        table = "recipient_channels"

    def __str__(self):
        return f"RecipientChannel [{self.id}] {self.name}"

    def __repr__(self):
        return f"RecipientChannel [{self.id}]"


class DonorChannel(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    channel_id = fields.CharField(max_length=100)
    is_active = fields.BooleanField(default=True)
    filters = fields.ReverseRelation["Filter"]
    recipient_channel = fields.ForeignKeyField("models.RecipientChannel", related_name="donor_channels")

    class Meta:
        table = "donor_channels"

    def __str__(self):
        return f"DonorChannel [{self.id}] {self.name}"

    def __repr__(self):
        return f"DonorChannel [{self.id}]"


class Forwarding(Model):
    id = fields.IntField(pk=True)
    recipient_channel = fields.ForeignKeyField("models.RecipientChannel", related_name="forwardings")
    donor_channel = fields.ForeignKeyField("models.DonorChannel", related_name="forwardings")
    datetime = fields.DatetimeField(auto_now_add=True)
    original_message_id = fields.BigIntField()
    forwarded_message_id = fields.BigIntField()

    class Meta:
        table = "forwardings"

    def __str__(self):
        return f"Forwarding [{self.id}] {self.recipient_channel.name} -> {self.donor_channel.name}"

    def __repr__(self):
        return f"Forwarding [{self.id}]"
