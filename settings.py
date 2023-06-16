from decouple import config

api_id = config("API_ID", cast=int)
api_hash = config("API_HASH")

db_url = f"{config('DB_DRIVER')}://{config('DB_USER')}:{config('DB_PASS')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"
TORTOISE_ORM = {
    "connections": {"default": db_url},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
