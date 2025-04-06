import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Log file path
log_file = os.path.join(log_dir, "strategy_debug.log")

# Configure rotating file handler (max 10MB per file, keep 5 backups)
handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - [%(name)s] %(message)s")
)

# Get root logger and attach handler
logging.basicConfig(level=logging.DEBUG, handlers=[handler])

# Suppress excessive logs from `watchdog`
logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)


# Function to get logger for a module
def get_logger(name):
    logger = logging.getLogger(name)
    return logger
