import logging

from pydantic import BaseSettings, BaseModel


class MQSettings(BaseModel):
    dsn: str


class LoggingSettings(BaseModel):
    level: str = logging.DEBUG
    format: str = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"


class Settings(BaseSettings):
    mq_settings: MQSettings
    priority: int
    worker_id: int
    logging: LoggingSettings = LoggingSettings()

    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
