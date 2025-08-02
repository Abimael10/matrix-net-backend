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

class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")

class TestConfig(GlobalConfig):
    DATABASE_URI: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True #Pretty much safe in a test database,
                                    #Also putting the hard coded test DB address
                                    #is not a high threat either, since it does not 
                                    #require a user auth and its records are a reflec of the code.
                                    #But PROD and DEV DBs stay hidden.
    SECRET_KEY: str = "test-secret-key-change-in-production"

    model_config = SettingsConfigDict(env_prefix="TEST_")

class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")

@lru_cache()
def get_config(env_state: str):
    configs = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
    return configs[env_state]()

#This will allow me to run it in test mode, will look for alts later
env_state = os.getenv("ENV", "test")
config = get_config(env_state)