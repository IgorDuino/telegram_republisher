from decouple import config
import hashlib

secret_key = config("SECRET_KEY")
debug = config("DEBUG", cast=bool)
log_level = config("LOG_LEVEL", default="INFO")
my_id = ''
secret_hash = hashlib.sha256(config("PASSWORD").encode()).hexdigest()

api_id = config("API_ID", cast=int)
api_hash = config("API_HASH")
session_name = config("SESSION_NAME")

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
