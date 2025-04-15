import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logger
log = logging.getLogger("ProfitMask")

# Set default log level (can be overridden by environment variable)
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
log.setLevel(getattr(logging, log_level, logging.DEBUG))

# File handler with rotation (5 MB max, 5 backups)
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "activity.log"), maxBytes=5 * 1024 * 1024, backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
log.addHandler(file_handler)
log.addHandler(console_handler)

log.info("Logger initialized")