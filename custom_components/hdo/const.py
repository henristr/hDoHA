"""Constants for the hDo integration."""

DOMAIN = "hdo"

# Supabase project config
SUPABASE_URL = "https://cylumkqhebudzifybxzz.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_cBMebp5ierBlMnivuwHTSQ_1iuJiyu8"

# Supabase REST endpoint for the todos table.
# Adjust TABLE_NAME if your table is not literally called "todos".
TABLE_NAME = "Todo"

SUPABASE_AUTH_TOKEN_URL = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
SUPABASE_AUTH_REFRESH_URL = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

UPDATE_INTERVAL_SECONDS = 60

# Field names as returned by Supabase (see example payload)
FIELD_ID = "id"
FIELD_CREATED_AT = "created_at"
FIELD_NAME = "name"
FIELD_IS_COMPLETED = "isCompleted"
FIELD_USER_ID = "user_id"
FIELD_CONTENT = "content"
