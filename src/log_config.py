from logging.config import dictConfig

from src.config import DevConfig, config

def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi.correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(config, DevConfig) else 32,
                    "default_value": "-"
                }
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s)%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s %(msecs)03dZ %(levelname)-8s [(%(correlation_id)s)] %(name)s %(lineno)d %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id"]
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024 * 5,  # 5MB
                    "backupCount": 5,
                    "encoding": "utf8",
                    "filters": ["correlation_id"]
                }
            },
            "loggers": {
                "src": {
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False
                },
                "databases": {"handlers": ["default", "rotating_file"], "level": "WARNING"},
                #Removing when I migrate to PostgreSQL
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"}
            },
        }
    )