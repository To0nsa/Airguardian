import logging

logger = logging.getLogger("airguardian")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
