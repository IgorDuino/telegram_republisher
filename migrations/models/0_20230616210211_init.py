from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "recipient_channels" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "channel_id" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "max_forwarding_per_day" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "donor_channels" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "channel_id" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "recipient_channel_id" INT NOT NULL REFERENCES "recipient_channels" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "filters" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "is_regex" BOOL NOT NULL  DEFAULT False,
    "pattern" VARCHAR(1000) NOT NULL,
    "replace_with" VARCHAR(1000),
    "is_active" BOOL NOT NULL  DEFAULT True,
    "action" VARCHAR(7) NOT NULL  DEFAULT 'REPLACE',
    "scope" VARCHAR(9) NOT NULL  DEFAULT 'RECIPIENT',
    "donor_channel_id" INT REFERENCES "donor_channels" ("id") ON DELETE CASCADE,
    "recipient_channel_id" INT REFERENCES "recipient_channels" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "filters"."action" IS 'SKIP: SKIP\nPAUSE: PAUSE\nREPLACE: REPLACE';
COMMENT ON COLUMN "filters"."scope" IS 'GLOBAL: GLOBAL\nRECIPIENT: RECIPIENT\nDONOR: DONOR';
CREATE TABLE IF NOT EXISTS "forwardings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "datetime" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "original_message_id" BIGINT NOT NULL,
    "forwarded_message_id" BIGINT NOT NULL,
    "donor_channel_id" INT NOT NULL REFERENCES "donor_channels" ("id") ON DELETE CASCADE,
    "recipient_channel_id" INT NOT NULL REFERENCES "recipient_channels" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
