# app/config.py
from pydantic import Field, AnyUrl, ValidationError
from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    fastapi_host: str             = Field("0.0.0.0", env="FASTAPI_HOST")
    fastapi_port: int             = Field(8000,      env="FASTAPI_PORT")
    database_url: str             = Field(...,       env="DATABASE_URL")
    x_secret: str               = Field(...,       env="X_SECRET")
    drones_api_url: AnyUrl        = Field(...,       env="DRONES_API_URL")
    users_api_url:  AnyUrl        = Field(...,       env="USERS_API_URL")
    celery_broker_url: AnyUrl     = Field(...,       env="CELERY_BROKER_URL")
    celery_result_backend: AnyUrl = Field(...,       env="CELERY_RESULT_BACKEND")
    debug: bool                   = Field(False,     env="DEBUG")

logger = logging.getLogger("uvicorn.error")

try:
	settings = Settings()
except ValidationError as e:
    logger.error("Invalid configuration:\n%s", e)
    raise SystemExit(1)

