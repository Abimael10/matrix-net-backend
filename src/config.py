from functools import lru_cache
from typing import Optional
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class GlobalConfig(BaseConfig):
    DATABASE_URI: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"

    # Mailtrap configuration
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_SERVER: str = "live.smtp.mailtrap.io"
    MAIL_PORT: int = 587

    #Backblaze B2 configuration
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None

    #Sentry
    #SENTRY_DSN: Optional[str] = None

class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_", extra="ignore")

class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_", extra="ignore")

class TestConfig(GlobalConfig):
    DATABASE_URI: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True #Pretty much safe in a test database,
                                    #Also putting the hard coded test DB address
                                    #is not a high threat either, since it does not 
                                    #require a user auth and its records are a reflec of the code.
                                    #But PROD and DEV DBs stay hidden.
    SECRET_KEY: str = "test-secret-key-change-in-production"
    # Provide default values for email configuration to avoid validation errors in test mode.
    MAIL_USERNAME: str = "test_username"
    MAIL_PASSWORD: str = "test_password"
    MAIL_FROM: str = "test@email.com"

    model_config = SettingsConfigDict(env_prefix="TEST_", extra="ignore")

@lru_cache()
def get_config(env_state: str):
    configs = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
    return configs[env_state]()

# Prefer test config automatically when running under pytest unless ENV is set
detected_env = os.getenv("ENV")
if not detected_env and os.getenv("PYTEST_CURRENT_TEST"):
    detected_env = "test"
env_state = detected_env or "dev"
config = get_config(env_state)
