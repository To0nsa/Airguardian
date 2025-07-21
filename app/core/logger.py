# app/core/logger.py

"""
This module defines a globally accessible logger..
"""

import logging

# Create or retrieve a logger named "airguardian"
logger = logging.getLogger("airguardian")

# Set the logging level to INFO (includes info, warning, error, critical)
logger.setLevel(logging.INFO)

# Create a stream handler to output logs to stdout (e.g. console or Docker logs)
handler = logging.StreamHandler()

# Define the log message format (timestamp, log level, logger name, and message)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

# Attach the formatter to the handler
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)
