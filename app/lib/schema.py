from tortoise import fields
from tortoise.models import Model


class Article(Model):
    id = fields.IntField(pk=True)
    version = fields.CharField(unique=True, max_length=26)  # ulid
    created_at = fields.DatetimeField(auto_now_add=True)
    date = fields.DatetimeField()
    url = fields.TextField()
    source_name = fields.TextField()
    title = fields.TextField()
    authors = fields.TextField()
    banner_img = fields.TextField()
    body = fields.TextField()
    summary = fields.TextField()
    errors = fields.BooleanField()
    parse_time = fields.FloatField()
    ner_time = fields.FloatField()
    fetch_time = fields.FloatField()

    class Meta:
        table = "articles"


class Keyword(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    keyword = fields.CharField(unique=True, max_length=512)
    count = fields.IntField()

    class Meta:
        table = "keywords"
