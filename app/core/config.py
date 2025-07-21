# app/core/config.py

"""
Application configuration loader using Pydantic BaseSettings.

This module defines the Settings class, which loads and validates environment
variables using Pydantic's BaseSettings. It ensures all required are present
and well-formed.
"""

# Import required classes and exceptions from Pydantic
from pydantic import Field, AnyUrl, ValidationError
from pydantic_settings import BaseSettings

# Import the project's central logger instance
from app.core.logger import logger

# Standard library module to terminate the app on fatal error
import sys

# NOTE:
# Uvicorn automatically loads environment variables from a `.env` file at startup
# when the `python-dotenv` package is installed.
# Therefore, we do not need to call `load_dotenv()` manually in most FastAPI setups.

# Define the application settings model
class Settings(BaseSettings):
    """
    Defines all environment-based configuration values for the application.

    Each field maps to a variable loaded from the environment (via a .env file or actual env vars).
    If a required field is missing or incorrectly typed, validation will fail at startup.
    """

    fastapi_host: str             = Field("0.0.0.0", env="FASTAPI_HOST")  # Server host
    fastapi_port: int             = Field(8000, env="FASTAPI_PORT")       # Server port
    database_url: str             = Field(..., env="DATABASE_URL")        # PostgreSQL connection string
    x_secret: str                 = Field(..., env="X_SECRET")            # Secret header value for secure endpoints

    drones_api_url: AnyUrl        = Field(..., env="DRONES_API_URL")     # External API: drone positions
    users_api_url:  AnyUrl        = Field(..., env="USERS_API_URL")      # External API: drone owner info

    celery_broker_url: AnyUrl     = Field(..., env="CELERY_BROKER_URL")  # Redis URL for Celery broker
    celery_result_backend: AnyUrl = Field(..., env="CELERY_RESULT_BACKEND")  # Redis URL for Celery result backend

    debug: bool                   = Field(False, env="DEBUG")             # Enable/disable FastAPI debug mode


# Try to load and validate all configuration values from environment
try:
    settings = Settings()  # Will raise ValidationError if any required field is missing or invalid
except ValidationError as e:
    # Log the detailed validation error and abort the application
    logger.error("Invalid configuration detected:\n%s", e)
    sys.exit("Startup aborted due to invalid configuration. Please check your .env file.")
