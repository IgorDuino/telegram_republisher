from tortoise import fields
from tortoise.models import Model

import re

from enum import Enum

from pyrogram.types import Message


class FilterAction(str, Enum):
    SKIP = "SKIP"
    PAUSE = "PAUSE"
    REPLACE = "REPLACE"

    def __str__(self):
        return self.value


class FilterScope(str, Enum):
    GLOBAL = "GLOBAL"
    RECIPIENT = "RECIPIENT"
    DONOR = "DONOR"

    def __str__(self):
        return self.value


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

    def check_on_text(self, text: str) -> bool:
        if self.is_regex:
            return re.search(self.pattern, text) is not None

        else:
            return self.pattern in text

    def check(self, msg: Message) -> bool:
        if msg.text:
            if self.check_on_text(msg.text):
                return True

        if msg.caption:
            if self.check_on_text(msg.caption):
                return True

        return False

    def apply_on_text(self, text: str) -> str:
        if self.action != FilterAction.REPLACE:
            raise Exception("Only REPLACE action is supported")

        if self.is_regex:
            return re.sub(self.pattern, self.replace_with, text)

        else:
            return text.replace(self.pattern, self.replace_with)

    def apply(self, msg: Message) -> Message:
        if self.action != FilterAction.REPLACE:
            raise Exception("Only REPLACE action is supported")

        if msg.text:
            msg.text = self.apply_on_text(msg.text)

        if msg.caption:
            msg.caption = self.apply_on_text(msg.caption)

        return msg

    @classmethod
    async def get_active_global_filters(cls):
        return await Filter.filter(is_active=True, scope=FilterScope.GLOBAL).all()

    class Meta:
        table = "filters"

    def __str__(self):
        return f"Filter [{self.id}] {self.name}: {'regex ' if self.is_regex else ''}'{self.pattern[:10]}' -> {self.replace_with[:10] if self.action == FilterAction.REPLACE else self.action}"

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

    async def get_active_filters(self):
        return await self.filters.filter(is_active=True).all()

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
    recipient_channel = fields.ForeignKeyField(
        "models.RecipientChannel", related_name="donor_channels", on_delete=fields.CASCADE
    )

    async def get_active_filters(self):
        return await Filter.filter(donor_channel=self, is_active=True).all()

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
