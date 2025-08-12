from functools import lru_cache
from typing import Optional
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class GlobalConfig(BaseConfig):
    DATABASE_URI: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    SECRET_KEY: Optional[str] = None

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
    SENTRY_DSN: Optional[str] = None

class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_", extra="ignore")

class ProdConfig(GlobalConfig):
    # Try multiple environment variable names for better deployment platform compatibility
    DATABASE_URI: Optional[str] = Field(
        default=None,
        validation_alias="DATABASE_URL"  # Most platforms use DATABASE_URL
    )
    SECRET_KEY: Optional[str] = Field(
        default=None,
        validation_alias="SECRET_KEY"  # Standard name
    )

    # Override other fields to try standard names first, then prefixed
    MAIL_USERNAME: Optional[str] = Field(default=None, validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = Field(default=None, validation_alias="MAIL_PASSWORD")
    MAIL_FROM: Optional[str] = Field(default=None, validation_alias="MAIL_FROM")

    B2_KEY_ID: Optional[str] = Field(default=None, validation_alias="B2_KEY_ID")
    B2_APPLICATION_KEY: Optional[str] = Field(default=None, validation_alias="B2_APPLICATION_KEY")
    B2_BUCKET_NAME: Optional[str] = Field(default=None, validation_alias="B2_BUCKET_NAME")

    SENTRY_DSN: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")

    model_config = SettingsConfigDict(extra="ignore")

    def model_post_init(self, __context):
        # First try DATABASE_URL (standard for most platforms like Render)
        if not self.DATABASE_URI:
            self.DATABASE_URI = os.getenv("DATABASE_URL")
        # Fallback to prefixed env vars if standard ones aren't set
        if not self.DATABASE_URI:
            self.DATABASE_URI = os.getenv("PROD_DATABASE_URI")
        if not self.SECRET_KEY:
            self.SECRET_KEY = os.getenv("PROD_SECRET_KEY")
        if not self.MAIL_USERNAME:
            self.MAIL_USERNAME = os.getenv("PROD_MAIL_USERNAME")
        if not self.MAIL_PASSWORD:
            self.MAIL_PASSWORD = os.getenv("PROD_MAIL_PASSWORD")
        if not self.MAIL_FROM:
            self.MAIL_FROM = os.getenv("PROD_MAIL_FROM")
        if not self.B2_KEY_ID:
            self.B2_KEY_ID = os.getenv("PROD_B2_KEY_ID")
        if not self.B2_APPLICATION_KEY:
            self.B2_APPLICATION_KEY = os.getenv("PROD_B2_APPLICATION_KEY")
        if not self.B2_BUCKET_NAME:
            self.B2_BUCKET_NAME = os.getenv("PROD_B2_BUCKET_NAME")
        if not self.SENTRY_DSN:
            self.SENTRY_DSN = os.getenv("PROD_SENTRY_DSN")

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
env_state = detected_env or "prod"
config = get_config(env_state)
