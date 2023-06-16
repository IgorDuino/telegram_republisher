from decouple import config

api_id = config("API_ID", cast=int)
api_hash = config("API_HASH")

TORTOISE_ORM = {
    "connections": {"default": config("DB_URL")},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
