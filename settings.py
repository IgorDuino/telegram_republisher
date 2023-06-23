from decouple import config
import hashlib

secret_key = config("SECRET_KEY")
debug = config("DEBUG", cast=bool)
log_level = config("LOG_LEVEL", default="INFO")
my_id = ""
secret_hash = hashlib.sha256(config("PASSWORD").encode()).hexdigest()

api_id = config("API_ID", cast=int)
api_hash = config("API_HASH")
session_name = config("SESSION_NAME")

db_url = f"postgres://{config('POSTGRES_USER')}:{config('POSTGRES_PASSWORD')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('POSTGRES_DB')}"
TORTOISE_ORM = {
    "connections": {"default": db_url},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
